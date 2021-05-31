import os
import json
import re
import subprocess
from datetime import datetime
import boto3

IS_DEBUG = bool(os.getenv('IS_DEBUG', 0))


def lambda_handler(event, context):
    BUCKET_NAME = os.getenv('CONFIG_S3_BUCKET_NAME')
    OBJECT_PATH = os.getenv('CONFIG_S3_OBJECT_PATH')
    SEND_TO = os.getenv('NOTICE_MAIL_TO')
    debug_print([BUCKET_NAME, OBJECT_PATH, SEND_TO])
    if not BUCKET_NAME or not OBJECT_PATH or not SEND_TO:
        print('Requrired Env val is not set')
        return

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    obj = bucket.Object(OBJECT_PATH)

    response = obj.get()
    body = response['Body'].read()

    confs = json.loads(body.decode('utf-8'))
    for conf in confs:
        domain = conf['domain']
        threshold_days = conf['days_to_notify']['warning']
        expire_date = get_cert_expire_date(domain)
        delta_date = expire_date - datetime.now()
        print("%s: %s days" % (domain, delta_date.days))

        if delta_date.days < threshold_days:
            subject = "Cert Expire Warning: %s" % domain
            body = "Warning: The SSL server certificate is disabled after %s days."\
                % delta_date.days
            debug_print(subject)
            res = send_email_by_ses(subject, [SEND_TO], body)
            debug_print(res)


def get_datetime(string):
    m = re.search(r'Not After : (.+)', string)
    return datetime.strptime(m.group(1), '%b %d %H:%M:%S %Y %Z')


def get_cert_expire_date(domain):
    command = "openssl s_client -connect %s:443 -servername %s < /dev/null " \
              "2> /dev/null | openssl x509 -text | grep 'Not After'" % (domain, domain)
    output = subprocess.check_output(command, shell=True)
    debug_print(output.decode())
    expire_date = get_datetime(output.decode())
    return expire_date


def send_email_by_ses(subject, recipients, text_body='', html_body=''):
    SEND_FROM = os.getenv('NOTICE_MAIL_FROM')

    msg = {
        'Subject': {
            'Data': subject,
            'Charset': 'UTF-8'
        },
        'Body': {}
    }

    if len(text_body) > 0:
        msg['Body']['Text'] =  {
            'Data': text_body,
            'Charset': 'UTF-8'
        }
    if len(html_body) > 0:
        msg['Body']['Html'] =  {
            'Data': html_body,
            'Charset': 'UTF-8'
        }

    SES_REGION = os.getenv('AWS_SES_REGION')
    client = boto3.client('ses', region_name=SES_REGION)
    src = SEND_FROM
    dest = {'ToAddresses': recipients}

    return client.send_email(Source=src, Destination=dest, Message=msg)


def debug_print(msg, prefix='!!!!!!!!! '):
    if not IS_DEBUG:
        return

    if isinstance(msg, list):
        for m in msg:
            print(prefix + m)
    elif isinstance(msg, dict):
        print(prefix + json.dumps(msg))
    else:
        print(prefix + msg)
