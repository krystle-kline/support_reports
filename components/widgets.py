import streamlit as st

def display_login_status(authenticator):
    if st.session_state["authentication_status"]:
        authenticator.logout('Log Out', 'main')
        st.write(f'Hey {st.session_state["name"]} :v:')
    elif st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    else:
        st.caption('Please file a support ticket or contact your digital producer if you need help accessing this app.')
    # with st.expander('Session state'):
    #     st.write(st.session_state)