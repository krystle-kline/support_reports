import streamlit as st
import auth

from components import display_login_status, display_admin_view, display_client_view


def main():
    st.set_page_config(layout="wide", page_icon=":bar_chart:")

    authenticator, auth_status, username, role, name, client_code = auth.authenticate_user(title='Made Media support reports')

    if role == 'admin':
        display_admin_view()
    elif role == 'client':
        display_client_view()

    footer = st.container()
    with footer:
        st.divider()
        display_login_status(authenticator)


if __name__ == "__main__":
    main()
