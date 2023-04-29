# components/admin_views.py

import streamlit as st
import pandas as pd
import datetime
import calendar

from components.widgets import display_ticket_card, display_tickets_aggrid
from freshdesk import get_tickets_data, status_mapping, get_agents, get_companies


def display_admin_view():
    st.sidebar.title("Filter Tickets")
    status_filter = st.sidebar.selectbox("Status", (None, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20), format_func=lambda x: status_mapping.get(x, "All") if not isinstance(status_mapping.get(x), int) else None)
    priority_filter = st.sidebar.selectbox("Priority", (None, 1, 2, 3, 4), format_func=lambda x: {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}.get(x, "All"))
    agent_filter = st.sidebar.selectbox("Agent", (None, *get_agents().keys()), format_func=lambda x: get_agents().get(x, "All"))

    today = datetime.date.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    modified_within = st.sidebar.date_input("Modified within", (first_day_of_month, last_day_of_month), min_value=first_day_of_month, max_value=last_day_of_month)
    modified_within = None

    company_filter = st.sidebar.multiselect("Company", options=get_companies().keys(), format_func=lambda x: get_companies().get(x))


    ticket_count = 0
    tickets_data_generator = get_tickets_data(
        status=status_filter,
        priority=priority_filter,
        agent_id=agent_filter,
        modified_within=modified_within,
        company_ids=company_filter)

    ticket_count_placeholder = st.empty()
    ticket_count_placeholder.markdown("Tickets in view: 0")

    for ticket in tickets_data_generator:
        display_ticket_card(ticket)
        ticket_count += 1
        ticket_count_placeholder.markdown(f"Tickets in view: {ticket_count}")

    


