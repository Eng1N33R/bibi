import httplib2
import os
import argparse

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from config import config

flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = config['APPLICATION_NAME']

spreadsheetId = config['SPREADSHEET']
    
def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.gcredentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'sheets-vk-python.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials

def acquire_auth():
    global service
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest'
                    '?version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

def get_range_values(cell_range):
    global service
    #pylint: disable=E1101
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=cell_range).execute()
    return result.get('values', [])

def get_cell_value(cell):
    return get_range_values(cell)[0][0]
