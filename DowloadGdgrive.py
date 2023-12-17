import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import pygsheets
import pandas as pd
from pydrive.drive import GoogleDrive
from bs4 import BeautifulSoup
from docx import Document
import json
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/drive.readonly",
          "https://www.googleapis.com/auth/drive.file"]


def download_file(real_file_id, download_path='D:/TI/api_google_drive/API-google-Drive'):
    creds = None
    # authentication
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)

        file_id = real_file_id
        file_metadata = service.files().get(fileId=file_id).execute()
        print(file_metadata['name'])

        # Lista arquivos no drive
        results = (
            service.files()
            .list(pageSize=15, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])
        if not items:
            print("No files found.")
            return
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")

        if 'application/vnd.google-apps.document' in file_metadata['mimeType']:
            download_and_convert_google_doc(file_id, download_path, creds)
        elif 'application/vnd.google-apps.spreadsheet' in file_metadata['mimeType']:
            download_and_convert_google_sheet(file_id, download_path, creds,file_metadata)
        else:
            request = service.files().get_media(fileId=file_id)
            file_extension = os.path.splitext(file_metadata['name'])[1]
            file_path = os.path.join(
                download_path, f"{file_id}{file_extension}")

            with open(file_path, "wb") as file:
                downloader = MediaIoBaseDownload(file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}.")

            print(f"O arquivo foi salvo em: {file_path}")

    except HttpError as error:
        print(f"Ocorreu um erro: {error}")


    def download_and_convert_google_doc(file_id, download_path, creds, file_metadata):
        service = build("drive", "v3", credentials=creds)

        request = service.files().export_media(fileId=file_id,
                                            mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        file_path = os.path.join(download_path, f"{file_metadata['name']}.docx")

        with open(file_path, "wb") as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}.")

        print(f"O documento DOCX foi salvo em: {file_path}")


def download_and_convert_google_sheet(file_id, download_path, creds,file_metadata):
    gc = pygsheets.authorize(service_file=None, credentials=creds)
    sh = gc.open_by_key(file_id)

    # Baixa a planilha como um DataFrame do pandas
    df = sh.sheet1.get_as_df()

    xlsx_path = os.path.join(download_path, f"{file_metadata['name']}.xlsx")

    # Salva o DataFrame como um arquivo XLSX
    df.to_excel(xlsx_path, index=False)

    print(f"A planilha XLSX foi salva em: {xlsx_path}")


if __name__ == "__main__":
    download_file(real_file_id="1_6dIs7pShAr8lE0cZXQNX7quiCpz002e81GDfU8NV_U")
