import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
import pytz
import requests
from bs4 import BeautifulSoup

RUBBISH_SYMBOL = '🗑️'
RECYCLING_SYMBOL = '♻️'

TRUE_SYMBOL = '✓'
FALSE_SYMBOL = '☓'

PLAIN_TEXT_MESSAGE_TEMPLATE = """\
                                Hello!

                                This is a reminder that your bins are due for collection tomorrow. You should put yours bins out tonight or before 7am tomorrow in order to ensure they are collected.

                                Collection Date: {collection_date}
                                Rubbish due: {rubbish_due}
                                Recycling due: {recycling_due}

                                Thanks,
                                RemindMeBot
                              """

HTML_MESSAGE_TEMPLATE = """\
                        <html>
                            <head>
                                <style type="text/css">
                                    .tg  {{border-collapse:collapse;border-spacing:0;border:none;}}
                                    .tg td{{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}}
                                    .tg th{{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}}
                                    .tg .tg-0pky{{border-color:inherit;text-align:left;vertical-align:top}}
                                    </style>
                            </head>
                            <body>
                                <p>Hello!</p>
                                <p>This is a reminder that your bins are due for collection tomorrow. You should put yours bins out tonight or before 7am tomorrow in order to ensure they are collected.</p>
                                
                                <table class="tg">
                                    <tr>
                                        <th class="tg-0pky">Collection Date</th>
                                        <th class="tg-0pky">{collection_date}</th>
                                    </tr>
                                    <tr>
                                        <td class="tg-0pky">Rubbish due</td>
                                        <td class="tg-0pky">{rubbish_due}</td>
                                    </tr>
                                    <tr>
                                        <td class="tg-0pky">Recycling due</td>
                                        <td class="tg-0pky">{recycling_due}</td>
                                    </tr>
                                </table>
                                <p>Thanks,</p>
                                <p>RemindMeBot</p>
                            </body>
                        </html>
                        """

SMTP_HOST = os.environ['SMTP_HOST']
SMTP_PORT = os.environ['SMTP_PORT']
SMTP_USERNAME = os.environ['SMTP_USERNAME']
SMPT_PASSWORD = os.environ['SMPT_PASSWORD']

FROM = os.environ['FROM']
TO = os.environ['TO']

URL = os.environ['URL']
URL_TIMEZONE = os.environ['URL_TIMEZONE']

TABLE_NAME = os.environ["TABLE_NAME"]
RECORD_KEY = "remindme-state"

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

TIMEZONE = pytz.timezone(URL_TIMEZONE)


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
    now = datetime.utcnow()
    datetime_format = "%A %d %B"
    loc_collection_date = datetime.strptime(date_elem.string, datetime_format)
    loc_collection_date = loc_collection_date.replace(year=now.year)
    loc_collection_date = TIMEZONE.localize(loc_collection_date)
    utc_collection_date = loc_collection_date.astimezone(pytz.utc)

    date_before_due_date = loc_collection_date - timedelta(days=1)
    date_before_due_date = date_before_due_date.date()

    # Only send a notification 1 day in advance
    if (date_before_due_date != now.date()):
        return

    last_item = None
    try:
        last_item = table.get_item(Key={'key': RECORD_KEY})['Item']
    except KeyError:
        # No document
        pass
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        # No previous state
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

            msg = MIMEMultipart('alternative')

            msg['From'] = FROM
            msg['To'] = TO
            msg['Subject'] = create_subject_text(is_rubbish_due,
                                                 is_recycling_due,
                                                 loc_collection_date)

            # Attach an HTML message with a fallback plain text message
            msg.attach(
                create_plain_text_message(is_rubbish_due, is_recycling_due,
                                          loc_collection_date))
            msg.attach(
                create_html_message(is_rubbish_due, is_recycling_due,
                                    loc_collection_date))

            # send the message via the server set up earlier.
            s.send_message(msg)
            s.close()
        except Exception as e:
            print("Error sending email: ", e)
        else:
            print(f'Email sent @ {utc_collection_date.isoformat()}')


def create_subject_text(rubbish, recycling, collection_date):
    message = f'Collection Reminder - {RUBBISH_SYMBOL}'

    if (recycling):
        message += RECYCLING_SYMBOL

    return message


def format_template(template, rubbish, recycling, collection_date):
    rubbish_due = TRUE_SYMBOL if rubbish else FALSE_SYMBOL
    recycling_due = TRUE_SYMBOL if recycling else FALSE_SYMBOL

    formatted = collection_date.strftime("%A %d %B")

    return template.format(rubbish_due=rubbish_due,
                           recycling_due=recycling_due,
                           collection_date=formatted)


def create_plain_text_message(rubbish, recycling, collection_date):
    return MIMEText(
        format_template(PLAIN_TEXT_MESSAGE_TEMPLATE, rubbish, recycling,
                        collection_date))


def create_html_message(rubbish, recycling, collection_date):
    return MIMEText(
        format_template(HTML_MESSAGE_TEMPLATE, rubbish, recycling,
                        collection_date), 'html')


def lambda_handler(event, context):
    main()


if __name__ == '__main__':
    main()
