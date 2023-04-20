import gspread
from google.oauth2 import service_account

def get_google_sheets_client(credentials_path):
    """Create a Google Sheets client using credentials from a JSON file."""
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/spreadsheets'])
    return gspread.authorize(scoped_credentials)

def read_client_data(sheet, client_id, year, month):
    """Read the client's monthly data from the Google Sheet."""
    records = sheet.get_all_records()
    for record in records:
        if record['ClientID'] == client_id and record['Year'] == year and record['Month'] == month:
            return record
    return None

def update_client_data(sheet, client_id, year, month, included_hours, used_hours, rollover_hours):
    """Update the client's monthly data in the Google Sheet."""
    row_index = None
    records = sheet.get_all_records()
    for index, record in enumerate(records):
        if record['ClientID'] == client_id and record['Year'] == year and record['Month'] == month:
            row_index = index + 2  # The row index is 2-based and includes header
            break

    if row_index is not None:
        sheet.update_cell(row_index, 4, included_hours)
        sheet.update_cell(row_index, 5, used_hours)
        sheet.update_cell(row_index, 6, rollover_hours)
    else:
        sheet.append_row([client_id, year, month, included_hours, used_hours, rollover_hours])
