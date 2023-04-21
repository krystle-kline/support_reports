import pandas as pd
import streamlit as st
import datetime
from config import base_url, status_mapping
from api import get_ticket_data, get_agent_data, get_requester_data
from utils import date_range_selector, get_paginated

api_key = st.secrets["api_key"]


def calculate_billable_time(time_entry, product_name="Unknown", change_request=False):
    # This function takes a time entry and returns the number of hours that should be billed.

    time_spent = time_entry["time_spent_in_seconds"] / 3600
    saas_products = ["BlocksOffice", "MonkeyWrench"]

    if change_request:
        return time_spent
        # If the ticket is marked as a change request, it's definitely billable
    elif product_name in saas_products:
        return 0
        # Then, if it's a SaaS product, it's not billable
    elif time_entry["billable"]:
        return time_spent
        # If it's not a SaaS product, and the time entry is marked as billable, it's billable
    else:
        return 0
        # Otherwise, it's not billable


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


def display_company_summary(selected_client, start_date):
    start_date_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    st.markdown(
        f'### {selected_client} — {start_date_datetime.strftime("%B %Y")}')


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

            tickets_details.append({
                "ticket_id": ticket_id,
                "title": ticket_data["subject"],
                "product": product_name,
                "status": status_name,
                "assigned_agent": agent_name,
                "requester_name": requester_name,
                "category": ticket_category,
                "change_request": change_request,
                "time_spent_this_month": time_entry["time_spent_in_seconds"] / 3600,
                "billable_time_this_month": calculate_billable_time(time_entry, product_name, change_request)
            })
        else:
            change_request = found_ticket.get("change_request", False)
            found_ticket["time_spent_this_month"] += time_entry["time_spent_in_seconds"] / 3600
            found_ticket["billable_time_this_month"] += calculate_billable_time(
                time_entry, product_name, change_request)

    return tickets_details


def display_time_summary(tickets_details_df):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total time this month",
                  f"{tickets_details_df['time_spent_this_month'].sum():.1f} hours")
    with col2:
        st.metric("Billable time this month",
                  f"{tickets_details_df['billable_time_this_month'].sum():.1f} hours")


def main():
    companies_data = get_companies_data()
    companies_options = get_companies_options(companies_data)
    products_data = get_products_data()
    product_options = get_product_options(products_data)

    selected_client, selected_value, start_date, end_date = display_client_selector(
        companies_options)
    display_company_summary(selected_client, start_date)

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
            tickets_details_df.set_index('ticket_id', inplace=True)

            display_time_summary(tickets_details_df)

            st.markdown("#### Tickets with time tracked this month")
            st.write(tickets_details_df)
        else:
            st.write("No time tracked for this month")
    else:
        st.write("No time tracked for this month")


if __name__ == "__main__":
    main()
