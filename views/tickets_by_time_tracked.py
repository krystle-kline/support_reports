import streamlit as st
from apis import freshdesk, googledocs
from utils import widgets

def display_report(client_code):
    
    # filters
    client_data = freshdesk.get_companies_data()
    clients = freshdesk.get_companies()
    col1, col2 = st.columns(2)
    if client_code == "admin":
        with col1:
            client_filter = st.selectbox("Client", clients)
    else:
        with col1:
            st.markdown("<small>Client</small>", unsafe_allow_html=True)
            client_freshdesk_id = freshdesk.find_id_by_client_code(client_code)
            client_name = next(
                (client['name'] for client in client_data if client["id"] == client_freshdesk_id), None)
            st.write(client_name)
    
    with col2: 
        start_date, end_date = widgets.date_range_selector()
        st.write (f"Start Date: {start_date}")
        st.write (f"End Date: {end_date}")
    

    # summary


    # report