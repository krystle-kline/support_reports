import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth

def authenticate_user(title: str = 'Login'):
    with open("auth.yaml") as f:
        auth = yaml.load(f, Loader=SafeLoader)
        authenticator = stauth.Authenticate(
            auth['credentials'],
            auth['cookie']['name'],
            auth['cookie']['key'],
            auth['cookie']['expiry_days'],
            auth['preauthorized']
        )

    name, authentication_status, username = authenticator.login(title, 'main')
    
    role = None
    client_code = None
    if authentication_status:
        role = auth['credentials']['usernames'][username].get('role', None)
        client_code = auth['credentials']['usernames'][username].get('client_code', None)
        st.session_state['role'] = role
        st.session_state['client_code'] = client_code

    return authenticator, authentication_status, username, role, name, client_code
