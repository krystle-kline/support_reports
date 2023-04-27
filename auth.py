# import streamlit_authenticator as stauth

# hashed_passwords = stauth.Hasher(['AlwaysBeBilling']).generate()

# print(hashed_passwords)

import yaml
from yaml.loader import SafeLoader
with open('auth.yaml', 'r') as f:
    auth_data = yaml.safe_load(f)

    credentials = auth_data['credentials']
    cookie_name = auth_data['cookie']['name']
    key = auth_data['cookie']['key']
    cookie_expiry_days = auth_data['cookie']['expiry_days']
    preauthorized = auth_data.get('preauthorized', {}).get('emails', [])

    role = {user: info['role'] for user, info in credentials['usernames'].items()}
