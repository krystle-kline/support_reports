import pandas as pd
import streamlit as st
import datetime
from config import base_url, status_mapping
from api import get_ticket_data, get_status_data, get_agent_data, get_requester_data
from utils import date_range_selector, get_paginated, get_data_from_api, calculate_billable_time

api_key = st.secrets["api_key"]

def main():
    companies_url = f'{base_url}/companies'
    companies_data = [page_data for sublist in get_paginated(companies_url, api_key) for page_data in sublist]
    companies_df = pd.DataFrame(companies_data)
    companies_options = dict(zip(companies_df['name'], companies_df['id']))

    with st.sidebar:
        selected_client = st.selectbox('Select a client', companies_options)
        selected_value = companies_options.get(selected_client)
        start_date, end_date = date_range_selector('Select a month and year', datetime.datetime.now()-datetime.timedelta(days=1080), datetime.datetime.now())

    start_date_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    f'''# Made Media support report'''
    f'''## {selected_client} — {start_date_datetime.strftime("%B %Y")}'''

    products_url = f'{base_url}/products'
    products_data = [page_data for sublist in get_paginated(products_url, api_key) for page_data in sublist]
    product_options = {product['id']: product['name'] for product in products_data}

    time_entries_url = f'{base_url}/time_entries?executed_before={end_date}&executed_after={start_date}&company_id={selected_value}'
    time_entries_data = [page_data for sublist in get_paginated(time_entries_url, api_key) for page_data in sublist]
    time_entries_df = pd.DataFrame(time_entries_data)

    if not time_entries_df.empty:
        time_entries_df = time_entries_df.astype({
            'id': 'str',
            'agent_id': 'str',
            'ticket_id': 'str',
            'company_id': 'str',
            'time_spent_in_seconds': 'str'
        })

    # st.experimental_show(time_entries_df)

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
                requester_data = get_requester_data(ticket_data["requester_id"])
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
                "time_spent_this_month": time_entry["time_spent_in_seconds"]/3600,
                "billable_time_this_month": calculate_billable_time(product_name, change_request, time_entry)
            })
        else:
            found_ticket["time_spent_this_month"] += time_entry["time_spent_in_seconds"]/3600
            found_ticket["billable_time_this_month"] += calculate_billable_time(product_name, change_request, time_entry)

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

        # two columns
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total time this month", f"{tickets_details_df['time_spent_this_month'].sum():.1f} hours")
        with col2:
            st.metric("Billable time this month", f"{tickets_details_df['billable_time_this_month'].sum():.1f} hours")

        st.experimental_show(tickets_details_df)
    else:
        st.write("No time tracked for this month")

    # total_time_spent = tickets_details_df['time_spent_this_month'].sum()
    # total_billable_time = tickets_details_df['billable_time_this_month'].sum()

    # st.markdown(f"**Total time spent this month: {total_time_spent:.2f} hours**")
    # st.markdown(f"**Total billable time this month: {total_billable_time:.2f} hours**")

    # st.write("## Tickets breakdown by product")
    # st.experimental_show(tickets_details_df.groupby("product").agg({"billable_time_this_month": "sum"}).sort_values("billable_time_this_month", ascending=False))

    # st.write("## Tickets breakdown by status")
    # st.experimental_show(tickets_details_df.groupby("status").agg({"billable_time_this_month": "sum"}).sort_values("billable_time_this_month", ascending=False))

    # st.write("## Tickets breakdown by agent")
    # st.experimental_show(tickets_details_df.groupby("assigned_agent").agg({"billable_time_this_month": "sum"}).sort_values("billable_time_this_month", ascending=False))

if __name__ == "__main__":
    main()
