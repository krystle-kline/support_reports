import streamlit as st

def display_admin_view():

    tab1, tab2 = st.tabs(["Billing App", "Ticket Browser"])

    with tab1:
        st.header("A cat")
        st.image("https://static.streamlit.io/examples/cat.jpg", width=200)

    with tab2:
        st.header("A dog")
        st.image("https://static.streamlit.io/examples/dog.jpg", width=200)