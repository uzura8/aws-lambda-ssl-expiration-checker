# SSL Expiration checker by Lambda + Python



## Preparation 

### Create IAM role

Create IAM role attached below policies and copy Arn

* AWSLambdaExecute
* AmazonS3ReadOnlyAccess
* AmazonSESFullAccess

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
    "CONFIG_S3_BUCKET_NAME": "your-config-bucket-name",
    "CONFIG_S3_OBJECT_PATH": "your-config-bucket-file-path.json",
    "AWS_SES_REGION": "ap-northeast-1",
    "NOTICE_MAIL_FROM": "from-your-address@example.com",
    "NOTICE_MAIL_TO": "to-your-address@example.com"
	...
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
pip install -r functions/requirements.txt -t functions/lib
````



### Execute on local

Execute lambda function on local

```bash
cd functions
python-lambda-local -t 30 -l lib -f lambda_handler lambda_function.py event.json
```

#### Options

* -t : timeout (seconds)
* -l : libraries dir



## Upload to Lambda

```bash
cd functions
lambda-uploader -r requirements.txt
```



## Trigger setting on Lambda Console

Add trigger by EventBridge on Lambda console
