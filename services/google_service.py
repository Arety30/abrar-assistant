import os
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleWorkspaceService:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/documents',
                       'https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/presentations']

    def _get_service(self, api_name, version, key_path_env, user_token=None):
        if user_token:
            creds = Credentials(token=user_token)
        else:
            key_path = os.getenv(key_path_env)
            if not key_path:
                raise Exception(f"API key path not set for {key_path_env}")
            creds = service_account.Credentials.from_service_account_file(
                key_path, scopes=self.scopes)
        return build(api_name, version, credentials=creds)

    def create_doc(self, title, user_token=None):
        service = self._get_service('docs', 'v1', 'GOOGLE_DOCS_API_KEY_PATH', user_token)
        doc = service.documents().create(body={'title': title}).execute()
        return f"https://docs.google.com/document/d/{doc.get('documentId')}"

    def create_spreadsheet(self, title, data=None, user_token=None):
        service = self._get_service('sheets', 'v4', 'GOOGLE_SPREADSHEETS_API_KEY_PATH', user_token)
        spreadsheet = service.spreadsheets().create(body={'properties': {'title': title}}).execute()
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet.get('spreadsheetId')}"

    def create_presentation(self, title, content=None, user_token=None):
        service = self._get_service('slides', 'v1', 'GOOGLE_SLIDES_API_KEY_PATH', user_token)
        presentation = service.presentations().create(body={'title': title}).execute()
        return f"https://docs.google.com/presentation/d/{presentation.get('presentationId')}"
