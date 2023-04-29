# components/widgets.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


def display_login_status(authenticator):
    if st.session_state["authentication_status"]:
        st.write(f'Hey {st.session_state["name"]} :v:')
        authenticator.logout('Log Out', 'main')
    elif st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    else:
        st.caption(
            'Please file a support ticket or contact your digital producer if you need help accessing this app.')


def display_ticket_card(ticket):
    ticket_id = ticket['id']
    ticket_link = f'https://mademedia.freshdesk.com/support/tickets/{ticket_id}'
    subject = ticket['subject']
    category = ticket['category']
    requester = ticket['requester']
    agent = ticket['responder']

    ticket_card_html = f'''
    <div style="border: 1px solid #ccc; border-radius: 5px; padding: 10px;">
        <h4><a href="{ticket_link}" target="_blank">{ticket_id}</a></h4>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Requester:</strong> {requester}</p>
        <p><strong>Agent:</strong> {agent}</p>
    </div>
    '''

    with st.container():
        st.markdown(ticket_card_html, unsafe_allow_html=True)


def display_tickets_aggrid(tickets_data):
    tickets_data_df = pd.DataFrame(tickets_data)

    gb = GridOptionsBuilder.from_dataframe(tickets_data_df)
    fd_ticket_link = JsCode("""
    function(id) {return `ID: ${id.value}`}
    """)

    gb.configure_column("id", cellRenderer=fd_ticket_link)
    gb.configure_column("first_column", header_name="First", editable=True)
    gb.configure_side_bar()
    gb.configure_pagination(
        enabled=True, paginationAutoPageSize=False, paginationPageSize=25)

    gb.configure_column(
        "id",
        maxWidth=60,
        type="numericColumn",
        label="ID",
        header_name="ID",
        pinned="left")
    gb.configure_column(
        "subject",
        header_name="Subject",
        cellStyle={'font-weight': 'bold'}
    )

    go = gb.build()

    AgGrid(
        tickets_data_df,
        gridOptions=go, allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False)
