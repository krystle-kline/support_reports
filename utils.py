import datetime
from datetime import timedelta
import streamlit as st
import requests

def date_range_selector(label, start_date, end_date):
    """
    A Streamlit widget for selecting a month and year, and returning the start
    and end dates of the selected month.
    """
    default_date = datetime.datetime.now().replace(day=1)
    month_options = [(datetime.datetime.now() - timedelta(days=30*i)).replace(day=1).strftime('%B %Y') for i in range(36)]
    selected_date = st.selectbox(label=label, options=month_options, index=0)
    selected_date = datetime.datetime.strptime(selected_date, '%B %Y').replace(day=1)
    start_date = selected_date.strftime('%Y-%m-%d')
    end_date = (selected_date.replace(day=28) + timedelta(days=4)).strftime('%Y-%m-%d')
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

def calculate_billable_time(product_name, change_request, time_entry):
    blocks_office = product_name == "BlocksOffice"
    is_change_request = change_request is not False

    if product_name == "BlocksOffice" and change_request is not False:
        return 0
    else:
        return time_entry["time_spent_in_seconds"]/3600 if time_entry["billable"] or is_change_request else 0
