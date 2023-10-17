import yaml
import streamlit_authenticator as stauth
import streamlit as st

from yaml.loader import SafeLoader


def authenticate_user():
    with open("auth.yaml") as f:
        auth = yaml.load(f, Loader=SafeLoader)
        authenticator = stauth.Authenticate(
            auth['credentials'],
            auth['cookie']['name'],
            auth['cookie']['key'],
            auth['cookie']['expiry_days'],
            auth['preauthorized']
        )

    with open('auth.yaml', 'r') as f:
        auth_data = yaml.safe_load(f)
        username = st.session_state.get('username', None)
        client_code = "—"
        name, authentication_status, username = authenticator.login('Login', 'main')
        if username:
            user = auth_data['credentials']['usernames'][username]
            client_code = user['client_code']

    auth_status = st.session_state.get("authentication_status", False)

    return auth_status, client_code, name, username, authenticator

    # if st.session_state.get("authentication_status", False):
    #     if client_code == "admin":
    #         tab1, tab2, tab3 = st.tabs(["Tickets by tracked time", "Tickets by status", "Export for Xero"])
    #         with tab1:
    #             display_monthly_dashboard(name)
    #         with tab3:
    #             display_xero_exporter()
    #         with tab2:
    #             display_ticket_search(client_code)
            
    #     else:
    #         tab1, tab2 = st.tabs(["Tickets by tracked time", "Tickets by status"])
    #         with tab1:
    #             display_monthly_dashboard(name)
    #         with tab2:
    #             display_ticket_search(client_code)
    #     st.write('---')
    #     f"You’re logged in as {name} ({username})"
    #     authenticator.logout('Logout', 'main')

    # elif st.session_state.get("authentication_status", False) == False:
    #     st.error('Username/password is incorrect')
    # elif st.session_state.get("authentication_status", None) == None:
    #     st.warning('Please enter your username and password').empty()
    # else:
    #     st.error("I don't know who you are 🤷‍♂️")