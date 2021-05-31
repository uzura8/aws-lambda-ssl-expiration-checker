# SSL Expiration checker by Lambda



## Preparation 

### Create IAM role

Create IAM role attached __"AmazonS3OutpostsReadOnlyAccess"__ and copy arn

### Required

You need below on local machine

- aws-cli >= 1.18.X
- Python >= 3.8



## Setup

### Setup for Lambda

Set Lambda config files

```bash
cp functions/lambda.json.sample functions/lambda.json
```

Edit functions/lambda.json for your env

```bash
{
  ...

  "region": "ap-northeast-1",
  "role": "arn:aws:iam::************:role/iam-role-lambda-development",
  "variables": {
    "CONFIG_S3_BUCKET_NAME": "site-monitoring-config",
    "CONFIG_S3_OBJECT_PATH": "domains_to_check_ssl_expiration.json",
    "AWS_SES_REGION": "ap-northeast-1",
    "SEND_FROM": "from-your-address@example.com",
    "SEND_TO": "to-your-address@example.com"
  }
}
```



## Local development

### Setup

Set config files

```bash
cp env.sh.sample env.sh
```

Edit env.sh for your local env

```bash
#!/bin/bash

export AWS_PROFILE="yuor-aws-profile-name"
export AWS_DEFAULT_REGION="ap-northeast-1"
...
```

Apply enviroment variables

```bash
# At project root dir
source env.sh
```

Setup venv

```bash
 python3 -m venv .
. bin/activate
```

Install pip packages

````bash
pip install -r requirements.txt
pip install -r functions/requirements.txt --target functions
````



### Execute on local

Execute lambda function on local

```bash
cd functions
python-lambda-local -f lambda_handler lambda_function.py event.json
```



## Upload to Lambda

```bash
cd functions
lambda-uploader
```



## Trigger setting on Lambda Console

hoge
