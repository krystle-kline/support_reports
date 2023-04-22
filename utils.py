import datetime
from datetime import timedelta
import calendar
import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials


def date_range_selector(label, start_date, end_date):
    """
    A Streamlit widget for selecting a month and year, and returning the start
    and end dates of the selected month.
    """
    default_date = datetime.datetime.now().replace(day=1)
    month_options = [(datetime.datetime.now() - timedelta(days=30*i)).replace(day=1).strftime('%B %Y') for i in range(48)]
    selected_date = st.selectbox(label=label, options=month_options, index=0)
    selected_date = datetime.datetime.strptime(selected_date, '%B %Y').replace(day=1)
    start_date = selected_date.strftime('%Y-%m-%d')
    last_day_of_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
    end_date = (selected_date.replace(day=last_day_of_month) + timedelta(days=1)).strftime('%Y-%m-%d')
    return start_date, end_date

def get_data_from_api(url, api_key):
    response = requests.get(url, auth=(api_key, 'X'))
    if response.ok:
        data = response.json()
        link_header = response.headers.get('link')
        return data, link_header
    else:
        return None, None

def get_paginated(url, api_key):
    data, link_header = get_data_from_api(url, api_key)
    if data is not None:
        yield data
        if link_header:
            next_url = link_header.split(';')[0].strip('<').strip('>')
            yield from get_paginated(next_url, api_key)

def get_currency_symbol(currency_code):
    currency_symbols = {
        'AUD': 'A$',
        'USD': '$',
        'CAD': 'C$',
        'GBP': '£',
        'EUR': '€'
    }
    return currency_symbols.get(currency_code, currency_code)


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


def get_client_data(worksheet, client_code):
    headers = worksheet.row_values(1)
    client_data = {}

    for row in worksheet.get_all_records():
        if row['client_code'] == client_code:
            client_data = row
            break

    return client_data

def get_contract_renews_date(worksheet, client_code):
    # Assuming client_code is in the first column
    client_codes = worksheet.col_values(1)
    for idx, code in enumerate(client_codes):
        if code == client_code:
            # Assuming contract_renews is in the second column
            contract_renews_date = worksheet.cell(idx + 1, 2).value
            return contract_renews_date
    return None