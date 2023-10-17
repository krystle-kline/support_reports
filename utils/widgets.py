import datetime
import streamlit as st
import calendar

def date_range_selector(start_date=datetime.datetime.now(
        ) - datetime.timedelta(days=1095), end_date=datetime.datetime.now()):
    default_date = datetime.datetime.now().replace(day=1)
    month_options = [(datetime.datetime.now() - datetime.timedelta(days=30*i)
                      ).replace(day=1).strftime('%B %Y') for i in range(48)]
    selected_date = st.selectbox(label="Choose Month", options=month_options, index=0)
    selected_date = datetime.datetime.strptime(
        selected_date, '%B %Y').replace(day=1)
    start_date = selected_date.strftime('%Y-%m-%d')
    last_day_of_month = calendar.monthrange(
        selected_date.year, selected_date.month)[1]
    end_date = (selected_date.replace(day=last_day_of_month) +
                datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    return start_date, end_date