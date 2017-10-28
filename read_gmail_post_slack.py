# coding: utf-8
from __future__ import print_function
import httplib2
import os
import base64
import email
import datetime
import subprocess
from config.config_data import *

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_from(mime_msg):
    from_str = email.header.decode_header(mime_msg.get('From'))
    addr = ""
    for f in from_str:
        if isinstance(f[0], bytes):
            addr += f[0].decode('utf-8')
        else:
            addr += f[0]
    return addr

def get_subject(mime_msg):
    subject = email.header.decode_header(mime_msg.get('Subject'))
    # print(subject)
    title = ""
    for sub in subject:
        if isinstance(sub[0], bytes):
            title = sub[0].decode(sub[1])
        else:
            title = sub[0]
    return title

def get_body(mime_msg):
    for part in mime_msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        body = ""
        charset = str(part.get_content_charset())
        if charset:
            tmp = unicode(part.get_payload(), charset)
            for line in tmp.split('\n'):
                if SEARCH_INDEX_STR in line:
                    body += line
    return body

def send_slack(msg):

    send_str =  "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"" + msg + "\"}' " + SLACK_WEBHOOK_URL
    print(send_str)
    subprocess.call(send_str, shell=True)

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    q_time = datetime.datetime.today() + datetime.timedelta(minutes=MINUTES)
    q_str = QSTRING + " after:" + q_time.strftime('%s')
    results = service.users().messages().list(userId='me', q=q_str).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        print('messages:')
        for message in messages:
            msg_raw = service.users().messages().get(userId='me', id=message["id"], format='raw').execute()

            # raw
            msg_str = base64.urlsafe_b64decode(msg_raw['raw'].encode('ASCII'))

            mime_msg = email.message_from_string(msg_str)
            # print(mime_msg.keys())

            # from
            addr = get_from(mime_msg)
            if addr != CHECK_ADDRESS:
                continue
            print(addr)

            # subject
            title = get_subject(mime_msg)
            if title != CHECK_SUBJECT:
                continue
            else:
                print(title)

            body = get_body(mime_msg)
            send_slack(body)
            print(body)


if __name__ == '__main__':
    main()
