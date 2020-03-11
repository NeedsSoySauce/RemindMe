# RemindMe

A short script to remind me what bins to take out for rubbish collection.

## Getting started

These steps will help you to deploy to AWS and/or setup a local environment for testing.

### Prerequisites

* pip
* pipenv
* awscli
* An AWS Lambda function to deploy to

### Installing

1. Install dependencies

```bash
pipenv install
```

2. Run the project locally

```bash
pipenv run python ./main.py
```

### Deployment

1. Install dependencies locally

```
pip install -t ./package requests bs4 html5lib
```

**Note:** You may need to use the `--system` flag if you're using debian.

2. Zip the script and it's dependencies into a deployment package

```bash
cp main.py package
cd package
zip -r package.zip *
```

3. Deploy to AWS

Replace "<func_name>" with the name of your lambda function.

```bash
aws lambda update-function-code --function-name <func_name> --zip-file fileb://package.zip 
```