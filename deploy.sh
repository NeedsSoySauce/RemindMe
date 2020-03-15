#!/bin/bash

FUNCTION_NAME="$1"

echo "Deploying to '$FUNCTION_NAME'"

# Install dependencies into packages folder
rm -r ./package
pip3 install -t ./package requests bs4 html5lib pytz

# Zip dependencies and main script file
cp main.py package 
cd package 
zip -r package.zip *

# Deploy to AWS
aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://package.zip 