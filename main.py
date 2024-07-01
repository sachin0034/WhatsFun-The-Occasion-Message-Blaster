import streamlit as st
from twilio.rest import Client
import json
import os
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

# MongoDB connection
mongo_client = MongoClient(os.getenv('MONGO_URI'))
db = mongo_client['guest_database']
collection = db['guests']

# JSON file to save messages
json_file = 'messages.json'

# Function to load existing messages
def load_messages():
    if os.path.exists(json_file):
        with open(json_file, 'r') as file:
            return json.load(file)
    return {"Birthday": "", "Anniversary": "", "Custom": []}

# Function to save messages
def save_messages(messages):
    with open(json_file, 'w') as file:
        json.dump(messages, file)

# Function to send WhatsApp message
def send_whatsapp_message(recipient_name, recipient_number, message_body):
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_='whatsapp:',
            body=message_body,
            to=f'whatsapp:{recipient_number}'
        )
        st.success(f"Message sent successfully to {recipient_name} ({recipient_number})! SID: {message.sid}")
    except Exception as e:
        st.error(f"Failed to send message to {recipient_name} ({recipient_number}): {str(e)}")

# Load existing messages
messages = load_messages()

# Streamlit app
st.title("Twilio WhatsApp Message Sender")

# Sidebar for custom messages
st.sidebar.title("Custom Messages")
option = st.sidebar.selectbox("Select Message Type", ["Birthday", "Anniversary", "Custom"])

if option == "Birthday":
    birthday_message = st.sidebar.text_area("Enter Birthday Message:", messages["Birthday"])
    if st.sidebar.button("Save Birthday Message"):
        messages["Birthday"] = birthday_message
        save_messages(messages)
        st.sidebar.success("Birthday message saved successfully!")

elif option == "Anniversary":
    anniversary_message = st.sidebar.text_area("Enter Anniversary Message:", messages["Anniversary"])
    if st.sidebar.button("Save Anniversary Message"):
        messages["Anniversary"] = anniversary_message
        save_messages(messages)
        st.sidebar.success("Anniversary message saved successfully!")

elif option == "Custom":
    custom_title = st.sidebar.text_input("Enter Custom Message Title:")
    custom_description = st.sidebar.text_area("Enter Custom Message Description:")
    if st.sidebar.button("Save Custom Message"):
        messages["Custom"].append({"Title": custom_title, "Description": custom_description})
        save_messages(messages)
        st.sidebar.success("Custom message saved successfully!")

# Input fields for sending message
st.subheader("Send WhatsApp Message")
template_option = st.selectbox("Select Message Template", ["Birthday", "Anniversary"] + [custom["Title"] for custom in messages["Custom"]])

# Function to process and send messages
def process_and_send_messages(data, selected_template):
    current_date = datetime.now().strftime("%Y-%m-%d")
    incorrect_template_used = False
    total_processed = 0

    for row in data:
        recipient_name = row.get('Name', row.get('name', '')).strip()
        recipient_number = row.get('Mobile Number', row.get('mobile_number', '')).replace(" ", "").strip()  # Remove spaces
        if not recipient_number.startswith("+"):
            recipient_number = "+" + recipient_number
        occasion_date = row.get('Occasion Date', row.get('birthday_date', row.get('anniversary_date', ''))).strip()
        occasion_type = row.get('Occasion Type', '').strip().lower()
        selected_template_lower = selected_template.strip().lower()

        # Convert dates to a common format for comparison
        try:
            occasion_date_obj = datetime.strptime(occasion_date, "%Y-%m-%d")
            current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
        except ValueError as ve:
            st.error(f"Date format error: {ve}")
            continue

        # Debug statements
        st.write(f"Selected Template: '{selected_template_lower}'")
        st.write(f"Occasion Type: '{occasion_type}'")
        st.write(f"Current Date: {current_date}")
        st.write(f"Occasion Date: {occasion_date}")
        st.write(f"Comparison Result: {selected_template_lower == occasion_type}")
        st.write(f"Occasion Date Object: {occasion_date_obj}")
        st.write(f"Current Date Object: {current_date_obj}")
        st.write(f"Date Comparison Result: {occasion_date_obj == current_date_obj}")

        if occasion_date_obj == current_date_obj:
            if selected_template_lower == occasion_type:
                message_body = ""
                if selected_template_lower == "birthday":
                    message_body = messages["Birthday"].replace("{name}", recipient_name).replace("{date}", occasion_date)
                elif selected_template_lower == "anniversary":
                    message_body = messages["Anniversary"].replace("{name}", recipient_name).replace("{date}", occasion_date)
                else:
                    for custom in messages["Custom"]:
                        if custom["Title"].strip().lower() == selected_template_lower:
                            message_body = custom["Description"].replace("{name}", recipient_name).replace("{date}", occasion_date)
                            break

                # Additional debug statements
                st.write(f"Message Body: '{message_body}'")

                if message_body:
                    send_whatsapp_message(recipient_name, recipient_number, message_body)
                    total_processed += 1
                else:
                    st.warning(f"No message body found for {recipient_name} ({recipient_number})")

            else:
                incorrect_template_used = True

    return incorrect_template_used, total_processed

# Option to fetch data from MongoDB
if st.button("Fetch and Send Messages from Database"):
    current_date = datetime.now().strftime("%Y-%m-%d")
    db_data = list(collection.find({
        "$or": [
            {"birthday_date": current_date},
            {"anniversary_date": current_date}
        ]
    }))
    if db_data:
        incorrect_template_used, total_processed = process_and_send_messages(db_data, template_option)
        if incorrect_template_used:
            st.warning("The selected template does not match the occasion type for some records. Please select the correct template.")
        if total_processed > 0:
            st.success(f"Processed {total_processed} records from the database.")
        else:
            st.info("No messages were sent because of template mismatches.")
    else:
        st.info("No matching records found in the database for today's date.")

# Upload CSV file (keep existing functionality)
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write(df)

    if st.button("Send Messages from CSV"):
        csv_data = df.to_dict('records')
        incorrect_template_used, total_processed = process_and_send_messages(csv_data, template_option)
        if incorrect_template_used:
            st.warning("The selected template does not match the occasion type for some records. Please select the correct template.")
        if total_processed > 0:
            st.success(f"Processed {total_processed} records from the CSV file.")
        else:
            st.info("No messages were sent because of template mismatches.")
