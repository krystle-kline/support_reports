import streamlit as st
import requests
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

@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting group data…")
def get_group_data(group_id):
    group_url = f'{base_url}/groups/{group_id}'
    group_data, _ = get_data_from_api(group_url, api_key)
    return group_data

@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting information about this Made product…")
def get_products_data():
    products_url = f'{base_url}/products'
    products_data = [page_data for sublist in get_paginated(
        products_url, api_key) for page_data in sublist]
    return products_data

def get_product_options(products_data):
    product_options = {product['id']: product['name']
                       for product in products_data}
    return product_options

@st.cache_resource(ttl=60*60*24*7, show_spinner="Getting requester data…")
def get_requester_data(requester_id):
    requester_url = f'{base_url}/contacts/{requester_id}'
    requester_data, _ = get_data_from_api(requester_url, api_key)
    return requester_data


def get_data_from_api(url, api_key):
    response = requests.get(url, auth=(api_key, 'X'))
    if response.ok:
        data = response.json()
        link_header = response.headers.get('link')
        return data, link_header
    else:
        return None, None


def get_paginated(url, api_key):
    data, link_header = get_data_from_api(url, api_key)
    if data is not None:
        yield data
        if link_header:
            next_url = link_header.split(';')[0].strip('<').strip('>')
            yield from get_paginated(next_url, api_key)