import pandas as pd
import streamlit as st
import datetime
from config import base_url, status_mapping
from api import get_ticket_data, get_agent_data, get_requester_data, get_group_data
from utils import date_range_selector, get_paginated
import gspread
from google.oauth2.service_account import Credentials

api_key = st.secrets["api_key"]


def calculate_billable_time(time_entry):
    # This function takes a time entry and returns the number of hours that should be billed to the client for it
    ticket_data = get_ticket_data(time_entry["ticket_id"])
    product_id = ticket_data["product_id"]
    product_name = get_product_options(get_products_data())[product_id]
    change_request = ticket_data["custom_fields"].get("change_request", False)
    time_spent = time_entry["time_spent_in_seconds"] / 3600
    saas_products = ["BlocksOffice", "MonkeyWrench"]
    unbillable_billing_statuses = ["Free", "90 Days", "Invoice"]
    billing_status = ticket_data["custom_fields"].get("billing_status")

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

def check_google_sheet(client_code):    
    client = setup_google_sheets()
    sheet = open_google_sheet(client, st.secrets["private_gsheets_url"])
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_records()
    st.write(data)


@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting client information…")
def get_companies_data():
    companies_url = f'{base_url}/companies'
    companies_data = []
    for page_data in get_paginated(companies_url, api_key):
        companies_data.extend(page_data)
    return companies_data


def get_companies_options(companies_data):
    companies_options = {}
    for company_data in companies_data:
        companies_options[company_data['name']] = company_data['id']
    return companies_options


@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting information about this Made product…")
def get_products_data():
    products_url = f'{base_url}/products'
    products_data = [page_data for sublist in get_paginated(
        products_url, api_key) for page_data in sublist]
    return products_data


def get_product_options(products_data):
    product_options = {product['id']: product['name']
                       for product in products_data}
    return product_options


@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting time entry information…")
def get_time_entries_data(start_date, end_date, selected_value):
    time_entries_url = f'{base_url}/time_entries?executed_before={end_date}&executed_after={start_date}&company_id={selected_value}'
    time_entries_data = [page_data for sublist in get_paginated(
        time_entries_url, api_key) for page_data in sublist]
    return time_entries_data


def display_client_selector(companies_options):
    col1, col2 = st.columns(2)
    with col1:
        selected_client = st.selectbox('Select a client', companies_options)
        selected_value = companies_options.get(selected_client)
    with col2:
        start_date, end_date = date_range_selector('Select a month and year', datetime.datetime.now(
        ) - datetime.timedelta(days=1080), datetime.datetime.now())
    return selected_client, selected_value, start_date, end_date


def display_company_summary(company_data):
    company_name = company_data['name']
    company_data_to_display = pd.DataFrame({
        'Client Code': company_data['custom_fields']['company_code'],
        'Support Contract': f"{company_data['custom_fields']['support_contract']}, paid annually" if company_data['custom_fields']['paid_annually'] else company_data['custom_fields']['support_contract'],
        'Included Hours Per Month': company_data['custom_fields']['inclusive_hours'],
        'Overage Rate': f"{company_data['custom_fields']['currency']} {company_data['custom_fields']['contract_hourly_rate']}/hour"
    }, index=[company_name]).transpose()
    f'# Made Media support report for {company_name}'
    st.dataframe(company_data_to_display)

def prepare_tickets_details(time_entries_data, product_options):
    tickets_details = []

    for time_entry in time_entries_data:
        ticket_id = time_entry['ticket_id']
        found_ticket = next(
            (item for item in tickets_details if item["ticket_id"] == ticket_id), None)

        if not found_ticket:
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
            billing_status = ticket_data["custom_fields"].get("billing_status", "Unknown")
            cf_client_deadline = ticket_data["custom_fields"].get("cf_client_deadline", None)
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

    return tickets_details




def display_time_summary(tickets_details_df, company_data):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total time this month",
                  f"{tickets_details_df['time_spent_this_month'].sum():.1f} hours")
    with col2:
        st.metric("Billable time this month",
                  f"{tickets_details_df['billable_time_this_month'].sum():.1f} hours")
    if not tickets_details_df[tickets_details_df["billing_status"] == "Invoice"].empty:
        invoice_tickets = tickets_details_df[tickets_details_df["billing_status"] == "Invoice"]
        num_invoice_tickets = len(invoice_tickets)
        if num_invoice_tickets == 1:
            ticket_id = invoice_tickets["ticket_id"].iloc[0]
            invoice_tickets_str = f"[#{ticket_id}](https://mademedia.freshdesk.com/support/tickets/{ticket_id})"
        else:
            invoice_ticket_ids = invoice_tickets["ticket_id"].tolist()
            invoice_tickets_str = ", ".join([f"[#{ticket_id}](https://mademedia.freshdesk.com/support/tickets/{ticket_id})" for ticket_id in invoice_ticket_ids])
        total_invoice_time = invoice_tickets["time_spent_this_month"].sum()
        total_invoice_time_str = "{:.1f}".format(total_invoice_time)
        st.warning(f"Ticket{'s' if num_invoice_tickets > 1 else ''} {invoice_tickets_str} {'are' if num_invoice_tickets > 1 else 'is'} marked with billing status ‘Invoice’ and {'have a total of' if num_invoice_tickets > 1 else 'has'} {total_invoice_time_str} hours tracked this month. This time is not included in the above total of billable hours.")



def main():
    companies_data = get_companies_data()
    companies_options = get_companies_options(companies_data)
    
    products_data = get_products_data()
    product_options = get_product_options(products_data)

    selected_client, selected_value, start_date, end_date = display_client_selector(
        companies_options)
    selected_company = next((company for company in companies_data if company["id"] == selected_value), None)
    company_data = {key: selected_company[key] for key in selected_company.keys()}
    
    display_company_summary(company_data)

    time_entries_data = get_time_entries_data(
        start_date, end_date, selected_value)
    time_entries_df = pd.DataFrame(time_entries_data)

    if not time_entries_df.empty:
        time_entries_df = time_entries_df.astype({
            'id': 'str',
            'agent_id': 'str',
            'ticket_id': 'str',
            'company_id': 'str',
            'time_spent_in_seconds': 'str'
        })

        tickets_details = prepare_tickets_details(
            time_entries_data, product_options)
        tickets_details_df = pd.DataFrame(tickets_details)

        if not tickets_details_df.empty:
            tickets_details_df = tickets_details_df.astype({
                'ticket_id': 'str',
                'title': 'str',
                'product': 'str',
                'status': 'str',
                'assigned_agent': 'str',
                'requester_name': 'str',
                'category': 'str',
                'change_request': 'bool',
                'time_spent_this_month': 'float',
                'billable_time_this_month': 'float'
            })
            # tickets_details_df.set_index('ticket_id', inplace=True)

            display_time_summary(tickets_details_df, company_data)

            st.markdown("#### Tickets with time tracked this month")

            formatted_tickets_details_df = tickets_details_df.copy()

            st.dataframe(formatted_tickets_details_df)
            
        else:
            st.write("Uh-oh, I couldn't find any tickets that match the time entries tracked this month. This probably means something is wrong with me 🤖")
    else:
        st.write("No time tracked for this month")


if __name__ == "__main__":
    main()