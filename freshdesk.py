# freshdesk.py
import streamlit as st
import requests
import pandas as pd
import urllib.parse
import datetime

from typing import List
from dateutil.parser import parse


domain = 'mademedia'
base_url = f'https://{domain}.freshdesk.com/api/v2'

status_mapping = {
    2: "Open",
    3: "Pending",
    4: "Resolved",
    5: "Closed",
    6: "Waiting on Customer",
    7: "7",
    8: "Awaiting Deploy",
    9: "Change for Tech Review",
    10: "10",
    11: "11",
    12: "Deferred",
    13: "Peer Review",
    14: "14",
    15: "15",
    16: "16",
    17: "17",
    18: "18",
    19: "19",
    20: "20"
}


api_key = st.secrets['api_key']
page_size = 100


@st.cache_resource(ttl=60*60*24*7, show_spinner=False)
def get_data_from_api(url, api_key):
    response = requests.get(url, auth=(api_key, 'X'))
    if response.ok:
        data = response.json()
        link_header = response.headers.get('link')
        return data, link_header
    else:
        print(
            f"Error fetching data from API. Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return None, None


def get_paginated(url, api_key):
    url = f'{url}'
    data, link_header = get_data_from_api(url, api_key)
    if data is not None:
        yield data
        if link_header:
            next_url = link_header.split(';')[0].strip('<').strip('>')
            yield from get_paginated(next_url, api_key)


def fetch_data(resource, api_key):
    url = f'{base_url}/{resource}'
    data = []
    for page_data in get_paginated(url, api_key):
        data.extend(page_data)
    return data


@st.cache_data(ttl=60*60*24*7, show_spinner=False)
def get_products():
    products_data = fetch_data('products', api_key)
    products = {product['id']: product['name'] for product in products_data}
    return products


@st.cache_data(ttl=60*60*24*7, show_spinner=False)
def get_agents():
    agents_data = fetch_data('agents', api_key)
    agents = {agent['id']: agent['contact'].get(
        'name') for agent in agents_data}
    return agents


@st.cache_data(ttl=60*60*24*7, show_spinner=False)
def get_companies():
    companies_data = fetch_data('companies', api_key)
    companies = {company['id']: company['name'] for company in companies_data}
    return companies


@st.cache_data(ttl=60*60*24*7, show_spinner=False)
def get_groups():
    groups_data = fetch_data('groups', api_key)
    groups = {group['id']: group['name'] for group in groups_data}
    return groups


@st.cache_data(ttl=60*60*24*7, show_spinner=False)
def get_contacts():
    contacts_data = fetch_data('contacts', api_key)
    contacts = {contact['id']: contact['name'] for contact in contacts_data}
    return contacts


def process_ticket(ticket):

    contact_name = get_contacts().get(ticket['requester_id'], "N/A")

    ticket = {
        'id': ticket['id'],
        'subject': ticket['subject'],
        'created_at': ticket['created_at'],
        'updated_at': ticket['updated_at'],
        'group_id': ticket['group_id'],
        'requester': contact_name,
        'requester_email': ticket['requester'].get('email') if ticket.get('requester') else "N/A",
        'responder': get_agents().get(ticket['responder_id']),
        'product': get_products().get(ticket['product_id']),
        'status': status_mapping.get(ticket['status'], 'Unknown'),
        'category': ticket['custom_fields'].get('category'),
        'type': ticket['type'],
        'due_by': ticket['due_by'],
        'fr_due_by': ticket['fr_due_by'],
        'tags': ticket['tags'],
        'change_request': ticket['custom_fields'].get('change_request'),
        'is_escalated': ticket['is_escalated'],
        'organisation': ticket['custom_fields'].get('organisation'),
        'client_deadline': ticket['custom_fields'].get('cf_client_deadline'),
        'cc_emails': ticket['cc_emails'],
        'fwd_emails': ticket['fwd_emails'],
        'reply_cc_emails': ticket['reply_cc_emails'],
        'ticket_cc_emails': ticket['ticket_cc_emails'],
        # 'stats_first_responded_at': ticket['stats'].get('first_responded_at'),
        # 'stats_resolved_at': ticket['stats'].get('resolved_at'),
        # 'stats_status_updated_at': ticket['stats'].get('status_updated_at'),
        # 'stats_closed_at': ticket['stats'].get('closed_at'),
    }
    return ticket


def get_tickets_data(updated_since=None, per_page=100, order_by='updated_at', order_type='desc', include='stats,requester,description', requester_id=None, company_id=None):
    url_params = {
        'per_page': per_page,
        'order_by': order_by,
        'order_type': order_type,
        'include': include
    }

    if updated_since is None:
        # Get tickets from the last 3 days
        date = datetime.datetime.now() - datetime.timedelta(days=3)
        date_utc = date.astimezone(datetime.timezone.utc)
        updated_since = date_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    if requester_id:
        url_params['requester_id'] = requester_id
    if company_id:
        url_params['company_id'] = company_id
    if updated_since:
        url_params['updated_since'] = updated_since

    query_string = '&'.join(
        [f"{key}={urllib.parse.quote(str(value))}" for key, value in url_params.items()])
    tickets_url = f'{base_url}/tickets?{query_string}'

    tickets_data = []
    for page_data in get_paginated(tickets_url, api_key):
        tickets_data.extend(page_data)

    return tickets_data


def search_tickets(status=None, priority=None, agent_id=None, group_id=None, tag=None, modified_within=None, company_ids: List[int] = None):
    query_parts = []

    if status is not None:
        query_parts.append(f"status:{status}")
    if priority is not None:
        query_parts.append(f"priority:{priority}")
    if agent_id is not None:
        query_parts.append(f"agent_id:{agent_id}")
    if modified_within is not None:
        start_date, end_date = modified_within
        query_parts.append(
            f"updated_at:> '{start_date.isoformat()}' AND updated_at:< '{end_date.isoformat()}'")
    if company_ids is not None and len(company_ids) > 0:
        company_query_parts = [
            f"company_id: {company_id}" for company_id in company_ids]
        company_query = " OR ".join(company_query_parts)
        query_parts.append(f"({company_query})")

    query_string = " AND ".join(query_parts)
    if not query_string:
        query_string = "updated_at:< '2021-01-01'"
    print(f"Generated query: {query_string}")

    tickets_url = f'{base_url}/search/tickets?query="{query_string}"'

    print(f"Tickets URL: {tickets_url}")
    tickets_generator = get_paginated(tickets_url, api_key)

    for tickets in tickets_generator:
        print(f"Tickets fetched: {len(tickets)}")
        if "results" in tickets:
            for ticket in tickets["results"]:
                print(f"Ticket object: {ticket}")
                processed_ticket = process_ticket(ticket)
                yield processed_ticket
        else:
            print("No results found in the `tickets` object.")
