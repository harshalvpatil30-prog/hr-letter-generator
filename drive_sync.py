import os
from paths import app_path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_NAME = "HR Letters"

TOKEN_PATH = app_path("token.json")
CREDS_PATH = app_path("credentials.json")

def get_service():
    """Log in (first run opens a browser) and return a Drive client."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(host="127.0.0.1", port=8080)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, name=FOLDER_NAME):
    """Find the folder by name, or create it the first time."""
    query = (f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' "
             "and trashed = false")
    found = service.files().list(q=query, fields="files(id)").execute().get("files", [])
    if found:
        return found[0]["id"]

    folder = service.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder"},
        fields="id",
    ).execute()
    return folder["id"]


def upload_pdf(path: str, service=None, folder_id=None) -> str:
    """Upload a PDF. Pass service/folder_id to reuse them across many uploads."""
    service = service or get_service()
    folder_id = folder_id or get_or_create_folder(service)

    media = MediaFileUpload(path, mimetype="application/pdf")
    uploaded = service.files().create(
        body={"name": os.path.basename(path), "parents": [folder_id]},
        media_body=media,
        fields="id, webViewLink",
    ).execute()
    return uploaded["webViewLink"]


if __name__ == "__main__":
    print("Uploaded:", upload_pdf("output/Experience_Letter_Rahul_Sharma_signed.pdf"))