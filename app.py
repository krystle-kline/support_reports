import streamlit as st
from utils import auth
from views import tickets_by_time_tracked
st.set_page_config(layout="wide")

def main():
    # authentication
    auth_status, client_code, name, username, authenticator = auth.authenticate_user()
    if auth_status == None:
        st.warning('Please enter your username and password').empty()
        return
    elif not auth_status:
        st.error("Username or password is incorrect")
        return
    
    # set up main app
    if username == "made":
        tab_labels = ["Tickets by Time Tracked", "Ticket Finder", "Export for Xero"]
    else:
        tab_labels = ["Tickets by Time Tracked", "Ticket Finder"]
        
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        tickets_by_time_tracked.display_report(client_code)
    
    with tabs[1]:
        st.write("Ticket Finder")
    
    if username == "made":
        with tabs[2]:
            st.write("Export for Xero")

    # footer
    st.write('---')
    f"You’re logged in as {name} (username `{username}`, client code `{client_code}`)"
    authenticator.logout('Log Out', 'main')

if __name__ == "__main__":
    main()