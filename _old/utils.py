import datetime
from datetime import timedelta
import calendar
import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from api import get_data_from_api, get_paginated, get_ticket_data, get_tickets_data, get_group_data, get_agent_data, get_requester_data, get_products_data, get_product_options
from config import base_url, status_mapping


def calculate_billable_time(time_entry):
    """
    Takes a time entry and returns the number of hours that should be billed to the client for it

    Args:
        time_entry (dict): A time entry from the FreshDesk API
    
    Returns:
        billable_time (float): The number of hours that should be billed to the client for this time entry
    """

    # Here's the data we need:
    ticket_data = get_ticket_data(time_entry["ticket_id"])
    product_id = ticket_data["product_id"]
    product_name = get_product_options(get_products_data())[product_id]
    change_request = ticket_data["custom_fields"].get("change_request", False)
    time_spent = time_entry["time_spent_in_seconds"] / 3600
    billing_status = ticket_data["custom_fields"].get("billing_status")

    # And here's some config:
    saas_products = ["BlocksOffice", "MonkeyWrench"]
    unbillable_billing_statuses = ["Free", "90 days", "Invoice"]

    # Now we can work out whether the time entry is billable or not:
    if billing_status in unbillable_billing_statuses:
        return 0
        # If the ticket is has one of these billing statuses in FreshDesk, it's definitely not billable
    elif change_request:
        return time_spent
        # Otherwise, if the ticket is marked as a change request, it's billable
    elif product_name in saas_products:
        return 0
        # Then, if it's a SaaS product, it's not billable
    elif time_entry["billable"]:
        return time_spent
        # If it's not a SaaS product, and the time entry is marked as billable, it's billable
    else:
        return 0
        # Otherwise, it's not billable



def date_range_selector(label, start_date, end_date):
    """
    A  widget for selecting a month and year, and returning the start and end dates of the selected month

    Args:
        label (str): The label for the widget
        start_date (str): The start date of the range, in the format YYYY-MM-DD
        end_date (str): The end date of the range, in the format YYYY-MM-DD
    
    Returns:
        start_date (str): The start date of the range, in the format YYYY-MM-DD
        end_date (str): The end date of the range, in the format YYYY-MM-DD
    """
    default_date = datetime.datetime.now().replace(day=1)
    month_options = [(datetime.datetime.now() - timedelta(days=30*i)
                      ).replace(day=1).strftime('%B %Y') for i in range(48)]
    selected_date = st.selectbox(label=label, options=month_options, index=0)
    selected_date = datetime.datetime.strptime(
        selected_date, '%B %Y').replace(day=1)
    start_date = selected_date.strftime('%Y-%m-%d')
    last_day_of_month = calendar.monthrange(
        selected_date.year, selected_date.month)[1]
    end_date = (selected_date.replace(day=last_day_of_month) +
                timedelta(days=1)).strftime('%Y-%m-%d')
    return start_date, end_date


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


def display_columns(time_summary_contents):
    num_columns = len(time_summary_contents)
    max_columns_per_row = 4 if num_columns == 4 else 3
    num_rows = (num_columns + max_columns_per_row - 1) // max_columns_per_row

    items = list(time_summary_contents.items())

    for row in range(num_rows):
        start_idx = row * max_columns_per_row
        end_idx = min(start_idx + max_columns_per_row, num_columns)
        cols = st.columns(end_idx - start_idx)

        for i, (label, value) in enumerate(items[start_idx:end_idx]):
            with cols[i]:
                st.metric(label, value)


def prepare_tickets_details(time_entries_data, product_options, progress=None, progress_text=None):
    """
    Get the details of the tickets that the time entries are associated with

    Args:
        time_entries_data (list): A list of time entries
        product_options (dict): A dictionary of product IDs and names
        progress (streamlit.Progress): An optional streamlit progress object
        progress_text (str or None): An optional streamlit progress text object
    
    Returns:
        tickets_details (list): A list of ticket details
    """
    tickets_details = []

    total_entries = len(time_entries_data)
    completed_entries = 0

    for time_entry in time_entries_data:
        ticket_id = time_entry['ticket_id']
        found_ticket = next(
            (item for item in tickets_details if item["ticket_id"] == ticket_id), None)

        if not found_ticket:
            progress_text = f"Getting data for ticket #{ticket_id}…"
            ticket_data = get_ticket_data(ticket_id)
            product_name = product_options.get(
                ticket_data["product_id"], "Unknown")
            status_name = status_mapping.get(ticket_data["status"], "Unknown")
            group_name = "Unknown"
            if ticket_data["group_id"]:
                group_id = ticket_data.get("group_id", None)
                group_data = get_group_data(ticket_data["group_id"])
                group_name = group_data["name"]
            agent_name = "Unknown"
            if ticket_data["responder_id"]:
                agent_data = get_agent_data(ticket_data["responder_id"])
                agent_name = agent_data["contact"]["name"]
            requester_name = "Unknown"
            if ticket_data["requester_id"]:
                requester_data = get_requester_data(
                    ticket_data["requester_id"])
                requester_name = requester_data["name"]
            change_request = ticket_data["custom_fields"].get(
                "change_request", False)
            ticket_category = ticket_data["custom_fields"].get(
                "category", "Unknown")
            ticket_type = ticket_data.get("type", "Unknown")
            billing_status = ticket_data["custom_fields"].get(
                "billing_status", "Unknown")
            cf_client_deadline = ticket_data["custom_fields"].get(
                "cf_client_deadline", None)
            tags = ticket_data.get("tags", [])

            tickets_details.append({
                "ticket_id": ticket_id,
                "status": status_name,
                "title": ticket_data["subject"],
                "requester_name": requester_name,
                "category": ticket_category,
                "type": ticket_type,
                "product": product_name,
                "change_request": change_request,
                "assigned_agent": agent_name,
                "group": group_name,
                "billing_status": billing_status,
                "cf_client_deadline": cf_client_deadline,
                "tags": tags,
                "time_spent_this_month": time_entry["time_spent_in_seconds"] / 3600,
                "billable_time_this_month": calculate_billable_time(time_entry)
            })
        else:
            change_request = found_ticket.get("change_request", False)
            found_ticket["time_spent_this_month"] += time_entry["time_spent_in_seconds"] / 3600
            found_ticket["billable_time_this_month"] += calculate_billable_time(
                time_entry)

    
        completed_entries += 1
        if progress:
            progress.progress(completed_entries / total_entries, text=progress_text)

    return tickets_details