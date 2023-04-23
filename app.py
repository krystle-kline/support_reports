import pandas as pd
import streamlit as st
import datetime
from config import base_url, status_mapping
from api import get_ticket_data, get_tickets_data, get_agent_data, get_requester_data, get_group_data, get_paginated, get_products_data, get_product_options, get_companies_data, get_companies_options, get_time_entries_data
from utils import date_range_selector, get_currency_symbol, setup_google_sheets, open_google_sheet, get_client_data, get_contract_renews_date, display_columns, get_product_options, prepare_tickets_details, calculate_billable_time

api_key = st.secrets["api_key"]


def display_client_selector(companies_options):
    col1, col2 = st.columns(2)
    with col1:
        selected_client = st.selectbox('Select a client', companies_options)
        selected_value = companies_options.get(selected_client)
    with col2:
        start_date, end_date = date_range_selector('Select a month and year', datetime.datetime.now(
        ) - datetime.timedelta(days=1080), datetime.datetime.now())
    return selected_client, selected_value, start_date, end_date


def display_company_summary(company_data, start_date):
    company_name = company_data['name']
    company_cfs = company_data['custom_fields']

    client_code = company_cfs['company_code']
    global client_info
    client_info = get_client_data(worksheet, client_code)

    contract_renews = client_info.get('contract_renews')

    try:
        client_renewal_date = datetime.datetime.strptime(
            contract_renews, "%B %Y")
        client_renewal_date_formatted = client_renewal_date.strftime("%B %Y")
    except:
        client_renewal_date_formatted = None

    company_data_to_display = {
        'Client Code': company_cfs['company_code'],
        'Support Contract': f"{company_cfs['support_contract']}, paid annually" if company_cfs['paid_annually'] else company_cfs['support_contract'],
        'Contract Renewal Date': client_renewal_date_formatted,
        'Included Hours Per Month': company_cfs['inclusive_hours'],
        'Overage Rate': f"{company_cfs['currency']} {company_cfs['contract_hourly_rate']}/hour"
    }
    formatted_date = datetime.datetime.strptime(
        start_date, '%Y-%m-%d').strftime('%B %Y')
    st.write(f'## {company_name} — {formatted_date}')
    
    col1, col2 = st.columns(2)
    with col1:
        "##### Data from FreshDesk:"
        company_data_to_display
    

    with col2:
        "##### Data from [Google Sheets](https://docs.google.com/spreadsheets/d/1Mv-7n-1ST9eFB3_q_rHQPt8NfcnsuqNYEM8ei5PXbgw/edit#gid=0):"
        client_info


def display_time_summary(tickets_details_df, company_data):
    year, month, _ = start_date.split("-")
    key = f"{year}_{month}_carryover"
    carryover_value = client_info.get(key)

    total_time = f"{tickets_details_df['time_spent_this_month'].sum():.1f} hours"
    billable_time = f"{tickets_details_df['billable_time_this_month'].sum():.1f} hours"

    rollover_time = "{:.1f} hours".format(float(carryover_value)) if carryover_value is not None and str(
        carryover_value).replace(".", "", 1).isdigit() else None
    net_time = "{:.1f} hours".format(tickets_details_df['billable_time_this_month'].sum(
    ) - (float(carryover_value) if carryover_value is not None and str(carryover_value).replace('.', '', 1).isdigit() else 0)) if carryover_value is not None else None

    now = datetime.datetime.now()
    start_date_year, start_date_month = map(int, start_date.split("-")[:2])
    is_current_or_adjacent_month = (
        now.year == start_date_year and abs(now.month - start_date_month) <= 1)
    currency_symbol = get_currency_symbol(
        company_data['custom_fields']['currency'])
    total_billable_hours = tickets_details_df['billable_time_this_month'].sum(
    ) - company_data['custom_fields'].get('inclusive_hours', 0)
    estimated_cost = f"{currency_symbol}{max(total_billable_hours - (float(carryover_value) if carryover_value is not None and str(carryover_value).replace('.', '', 1).isdigit() else 0), 0) * (company_data['custom_fields']['contract_hourly_rate']) if is_current_or_adjacent_month and company_data['custom_fields']['contract_hourly_rate'] is not None else 0.00:,.2f}"

    time_summary_contents = {
        "Total time this month": total_time,
        "Billable time this month": billable_time,
    }

    if rollover_time is not None:
        time_summary_contents["Rollover time available"] = rollover_time

    if is_current_or_adjacent_month and company_data['custom_fields']['contract_hourly_rate'] is not None:
        time_summary_contents["Estimated cost this month"] = estimated_cost

    display_columns(time_summary_contents)

    # warn if any tickets with time tracked are marked "Invoice"
    if not tickets_details_df[tickets_details_df["billing_status"] == "Invoice"].empty:
        invoice_tickets = tickets_details_df[tickets_details_df["billing_status"] == "Invoice"]
        num_invoice_tickets = len(invoice_tickets)
        if num_invoice_tickets == 1:
            ticket_id = invoice_tickets["ticket_id"].iloc[0]
            invoice_tickets_str = f"[#{ticket_id}](https://mademedia.freshdesk.com/support/tickets/{ticket_id})"
        else:
            invoice_ticket_ids = invoice_tickets["ticket_id"].tolist()
            invoice_tickets_str = ", ".join(
                [f"[#{ticket_id}](https://mademedia.freshdesk.com/support/tickets/{ticket_id})" for ticket_id in invoice_ticket_ids])
        total_invoice_time = invoice_tickets["time_spent_this_month"].sum()
        total_invoice_time_str = "{:.1f}".format(total_invoice_time)
        st.warning(f"Ticket{'s' if num_invoice_tickets > 1 else ''} {invoice_tickets_str} {'are' if num_invoice_tickets > 1 else 'is'} marked with billing status ‘Invoice’ and {'have a total of' if num_invoice_tickets > 1 else 'has'} {total_invoice_time_str} hours tracked this month. This time is not included in the above total of billable hours.")


def main():
    st.set_page_config(layout="wide", page_icon=":bar_chart:")
    st.title("Made Media support report")

    client = setup_google_sheets()
    sheet = open_google_sheet(client, st.secrets["private_gsheets_url"])
    global worksheet
    worksheet = sheet.get_worksheet(0)

    companies_data = get_companies_data()
    companies_options = get_companies_options(companies_data)
    products_data = get_products_data()
    product_options = get_product_options(products_data)

    global start_date
    selected_client, selected_value, start_date, end_date = display_client_selector(
        companies_options)
    selected_company = next(
        (company for company in companies_data if company["id"] == selected_value), None)
    company_data = {key: selected_company[key]
                    for key in selected_company.keys()}

    display_company_summary(company_data, start_date)

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

            display_time_summary(tickets_details_df, company_data)

            st.markdown("#### Tickets with time tracked this month")

            formatted_tickets_details_df = tickets_details_df.copy()

            formatted_tickets_details_df = (
                formatted_tickets_details_df.style
                .format(precision=1)
            )
            formatted_tickets_details_df

        else:
            st.write("Uh-oh, I couldn't find any tickets that match the time entries tracked this month. This probably means something is wrong with me 🤖")

    else:
        st.write("No time tracked for this month")


if __name__ == "__main__":
    main()
