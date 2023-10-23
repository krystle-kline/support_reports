import gspread
from google.oauth2.service_account import Credentials

def setup_google_sheets():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    return client


def open_google_sheet(client, url):
    sheet = client.open_by_url(url)
    return sheet