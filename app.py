import streamlit as st
import auth

from components import display_login_status


def main():
    st.set_page_config(layout="wide", page_icon=":bar_chart:")

    authenticator, auth_status, username, role, name, client_code = auth.authenticate_user(title='Made Media support reports')
    display_login_status(authenticator)
    st.write(auth_status)
    if auth_status and role == 'admin':
        st.write('You are an admin')
    elif auth_status and role == 'client':
        st.write(f'Your client code is {client_code}')
    


if __name__ == "__main__":
    main()
