import os
import json
import socket
import ssl
import time
import datetime
import pytz
import boto3

IS_DEBUG = bool(os.getenv('IS_DEBUG', '0'))
jst = pytz.timezone('Asia/Tokyo')


def lambda_handler(event, context):
    BUCKET_NAME = os.getenv('CONFIG_S3_BUCKET_NAME')
    OBJECT_PATH = os.getenv('CONFIG_S3_OBJECT_PATH')
    SEND_TO = os.getenv('NOTICE_MAIL_TO')
    SLEEP_TIME_SEC = int(os.getenv('SLEEP_TIME_SEC', 0))
    debug_print([BUCKET_NAME, OBJECT_PATH, SEND_TO, SLEEP_TIME_SEC])
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
        if not conf['is_enabled']:
            continue

        domain = conf['domain']
        days = conf['days_to_notify']

        is_notice, state, msg, expire_date, remaining =\
                check_ssl_expired(domain,  days['warning'], days['alert'])
        print('%s: %s' % (domain, remaining))

        if is_notice:
            send_notice_mail([SEND_TO], domain, state, expire_date, msg)

        if SLEEP_TIME_SEC:
            time.sleep(SLEEP_TIME_SEC)

def check_ssl_expired(domain, warning_days, alert_days):
    remaining, expires = get_ssl_expiration_remaining(domain)
    remaining_days = remaining.days
    expire_date = expires.strftime('%Y/%m/%d')

    is_notice = False
    state = 'success'
    msg = 'Expire in %s days' % remaining_days
    if remaining < datetime.timedelta(days=0):
        is_notice = True
        state = 'critical'
        msg = 'Already Expired!'

    elif remaining < datetime.timedelta(days=alert_days):
        is_notice = True
        state = 'alert'

    elif remaining < datetime.timedelta(days=warning_days):
        is_notice = True
        state = 'warning'

    return is_notice, state, msg, expire_date, remaining_days


def get_ssl_expiration_remaining(domain):
    expires = get_ssl_expiration_datetime(domain)
    return expires - datetime.datetime.now(jst), expires


def get_ssl_expiration_datetime(domain):
    date_fmt = r'%b %d %H:%M:%S %Y %Z'
    utc_datetime = datetime.datetime.strptime(get_ssl_expiration(domain), date_fmt)
    return utc_datetime.astimezone(jst)


def get_ssl_expiration(domain):
    debug_print('connect {}'.format(domain))
    SOCKET_TIMEOUT_SEC = float(os.getenv('SOCKET_TIMEOUT_SEC', 3))
    context = ssl.create_default_context()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            ssock.settimeout(SOCKET_TIMEOUT_SEC)
            ssock.connect((domain, 443))
            ssl_info = ssock.getpeercert()
            ssock.close()
            debug_print(ssl_info)
            return ssl_info['notAfter']


def send_notice_mail(recipients, domain, state, expire_date, msg):
    subject = 'SSL Expire %s: %s' % (state.capitalize(), domain)
    body = """\
    Domin: %s
    State: %s
    Expiration: %s
    Message: %s""" % (domain, state.capitalize(), expire_date, msg)

    debug_print(subject)
    debug_print(body)
    send_email_by_ses(recipients, subject, text_body=body)


def send_email_by_ses(recipients, subject, text_body='', html_body=''):
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
        print(prefix + json.dumps(msg))
    elif isinstance(msg, dict):
        print(prefix + json.dumps(msg))
    else:
        print(prefix + str(msg))
