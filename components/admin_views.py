# components/admin_views.py

import streamlit as st
import pandas as pd
import datetime
import calendar
from dateutil.relativedelta import relativedelta

from components.widgets import display_ticket_card, display_tickets_aggrid
from freshdesk import get_tickets_data, status_mapping, get_agents, get_companies, get_useful_ticket_data



def get_start_end_dates(option):
    today = datetime.date.today()
    if option == "Today":
        start_date = today
        end_date = today
    elif option == "Past 7 days":
        start_date = today - datetime.timedelta(days=6)
        end_date = today
    elif "calendar month" in option:
        this_month = datetime.date(today.year, today.month, 1)
        if option == "This calendar month":
            start_date = this_month
        else:
            start_date = this_month - relativedelta(months=1)
        end_date = start_date + relativedelta(months=1) - datetime.timedelta(days=1)
    else:
        start_date = None
        end_date = None
    return start_date, end_date



def display_admin_view():

    with st.sidebar:
        client_list = ["All"] + list(get_companies().values())
        client = st.selectbox("Client", client_list)
        current_month = datetime.date.today().strftime("%B %Y")
        last_month = (datetime.date.today() - relativedelta(months=1)).strftime("%B %Y")
        options = ["Today", "Past 7 days", f"{current_month}", f"{last_month}", "Custom range"]

        selected_option = st.selectbox("Modified within", options)
        start_date, end_date = get_start_end_dates(selected_option)

        if selected_option == "Custom range":
            start_date = st.date_input("Start date", start_date)
            end_date = st.date_input("End date", end_date)

        st.write(f"Selected range: {start_date} to {end_date}")



    ticket_data = get_tickets_data()
    tickets = [get_useful_ticket_data(ticket) for ticket in ticket_data]
    df = pd.DataFrame(tickets)
    st.write(df)

    # st.write(tickets)


    # ticket_count = 0
    # tickets_data_generator = get_tickets_data(
    #     status=status_filter,
    #     priority=priority_filter,
    #     agent_id=agent_filter,
    #     modified_within=modified_within,
    #     company_ids=company_filter)

    # ticket_count_placeholder = st.empty()
    # ticket_count_placeholder.markdown("Tickets in view: 0")

    # for ticket in tickets_data_generator:
    #     display_ticket_card(ticket)
    #     ticket_count += 1
    #     ticket_count_placeholder.markdown(f"Tickets in view: {ticket_count}")

    


