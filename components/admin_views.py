# components/admin_views.py

import streamlit as st
import pandas as pd
import datetime
import calendar

from components.widgets import display_ticket_card, display_tickets_aggrid
from freshdesk import get_tickets_data, status_mapping, get_agents, get_companies, process_ticket


def display_admin_view():

    tickets = get_tickets_data()
    processed_tickets = [process_ticket(ticket) for ticket in tickets]
    df = pd.DataFrame(processed_tickets)
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

    


