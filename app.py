import streamlit as st
import pandas as pd
import datetime
import streamlit_authenticator as stauth

def main():
    # authentication

    user = authenticate_user()