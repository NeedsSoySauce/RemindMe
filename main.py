import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup
import boto3

SMTP_HOST = os.environ['SMTP_HOST']
SMTP_PORT = os.environ['SMTP_PORT']
SMTP_USERNAME = os.environ['SMTP_USERNAME']
SMPT_PASSWORD = os.environ['SMPT_PASSWORD']

SENDER = os.environ['SENDER']

URL = os.environ['URL']

RECORD_KEY = "remindme-state"

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RemindMeState')


def main():
    response = requests.get(URL)

    soup = BeautifulSoup(response.text, 'html5lib')

    # Find parent container for household disposal
    container = soup.find('h3', class_="card-title h2").parent.parent
    link_container = container.find('div', class_="links")

    # Get date
    date_elem = link_container.find('span', class_="m-r-1")

    # Get what items are due
    is_rubbish_due = link_container.find('span', class_='icon-rubbish') != None
    is_recycling_due = link_container.find('span',
                                           class_='icon-recycle') != None

    # Parse date into a datetime object
    datetime_format = "%A %d %B"
    collection_date = datetime.strptime(date_elem.string, datetime_format)
    collection_date = collection_date.replace(year=datetime.now().year)

    last_item = None
    try:
        last_item = table.get_item(Key={'key': RECORD_KEY})['Item']
    except KeyError:
        # No document
        pass

    if last_item is None or \
       last_item['rubbish'] != is_rubbish_due or \
       last_item['recycling'] != is_recycling_due:

        table.put_item(
            Item={
                'key': RECORD_KEY,
                'rubbish': is_rubbish_due,
                'recycling': is_recycling_due
            })

        try:
            s = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT)
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(SMTP_USERNAME, SMPT_PASSWORD)

            msg = MIMEMultipart()

            msg['From'] = SENDER
            msg['To'] = SENDER
            msg['Subject'] = "Reminder"

            msg.attach(MIMEText(generate_message(is_rubbish_due, is_recycling_due)))

            # send the message via the server set up earlier.
            s.send_message(msg)
            s.close()
        except Exception as e:
            print("Error sending email: ", e)
        else:
            print("Email sent!")

def generate_message(rubbish, recycling):
    message = ""

    if (rubbish):
        message += "Rubbish due"

    if (recycling):
        message += "Recycling due"

    return message

def lambda_handler(event, context):
    main()


if __name__ == '__main__':
    main()
