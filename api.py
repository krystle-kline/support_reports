import streamlit as st
from utils import get_data_from_api, get_paginated
from config import base_url

api_key = st.secrets["api_key"]

@st.cache_resource(ttl=60*60, show_spinner="Getting ticket data…")
def get_ticket_data(ticket_id):
    ticket_url = f'{base_url}/tickets/{ticket_id}'
    ticket_data, _ = get_data_from_api(ticket_url, api_key)
    return ticket_data

@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting agent data…")
def get_agent_data(agent_id):
    agent_url = f'{base_url}/agents/{agent_id}'
    agent_data, _ = get_data_from_api(agent_url, api_key)
    return agent_data

@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting requester data…")
def get_requester_data(requester_id):
    requester_url = f'{base_url}/contacts/{requester_id}'
    requester_data, _ = get_data_from_api(requester_url, api_key)
    return requester_data