import os
import io
import pickle
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def authenticate_drive():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)


def list_folder_contents(service, folder_id):
    items = []
    page_token = None
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        items.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break
    return items


def download_pdf(service, file_id, filename, output_path):
    os.makedirs(output_path, exist_ok=True)
    filepath = os.path.join(output_path, filename)
    request = service.files().get_media(fileId=file_id)
    with open(filepath, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {filename}: {int(status.progress() * 100)}%")


def traverse_and_download(service, folder_id, local_path):
    contents = list_folder_contents(service, folder_id)
    for item in contents:
        name = item['name']
        file_id = item['id']
        mime = item['mimeType']
        if mime == 'application/vnd.google-apps.folder':
            # Create local subfolder
            subfolder_path = os.path.join(local_path, name)
            traverse_and_download(service, file_id, subfolder_path)
        elif mime == 'application/pdf':
            download_pdf(service, file_id, name, local_path)
        else:
            print(f"Skipping {name} (not a PDF or folder)")

service = authenticate_drive()
traverse_and_download(service, ROOT_FOLDER_ID, LOCAL_BASE)
