# RemindMe

A short script to remind me what bins to take out for rubbish collection.

## Getting started

These steps will help you to deploy to AWS and/or setup a local environment for testing.

### Prerequisites

* pip
* pipenv
* awscli
* An AWS Lambda function to deploy to
* A DynamoDB table to store the previous state of the page being scraped

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

Run the included `deploy.sh` script.

```bash
.\deploy.sh <function_name>
```