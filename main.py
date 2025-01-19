# Import your dependencies
from dotenv import load_dotenv
import os
from nylas import Client
from flask import Flask, request, redirect, url_for, session, jsonify
from flask_session.__init__ import Session
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest
import requests  # Add this to your imports at the top
from bs4 import BeautifulSoup
import re


# Load your env variables
load_dotenv()

def clean_email(html_content):
    # Clean HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ')
    
    # Clean whitespace
    # Step 1: Remove excessive newlines
    text = re.sub(r'\n\s*\n+', '\n', text)
    
    # Step 2: Strip leading/trailing whitespace on each line
    text = '\n'.join(line.strip() for line in text.splitlines())
    
    # Step 3: Remove multiple spaces and invisible characters
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r'\u200b|\u200c|\u200d|‌|​', '', text)  # Remove zero-width spaces and similar
    
    # Step 4: Remove leading/trailing whitespace
    return text.strip()


def get_emails_recent(limit=1):
    nylas = Client(
    os.environ.get('NYLAS_API_KEY'),
    os.environ.get('NYLAS_API_URI')
    )

    emails = []

    grant_id = os.environ.get("NYLAS_GRANT_ID")

    messages = nylas.messages.list(
    grant_id,
    query_params={
        "limit": limit
        }
    )
    for page in messages:
        for msg in page:
            if str(type(msg)) == "<class 'nylas.models.messages.Message'>":
                email_data = {
                "subject": "",
                "from": "",
                "to": "",
                "body": "",
                "date": ""
                }
                # email_data["ID"] = msg.id
                email_data["subject"] = msg.subject
                # email_data["Snippet"] = msg.snippet
                email_data["from"] = msg.from_
                email_data["to"] = msg.to
                email_data["body"] = clean_email(msg.body)
                email_data["date"] = msg.date
                # email_data_str = f"ID: {email_data['ID']}, Subject: {email_data['Subject']}, Snippet: {email_data['Snippet']}, From: {email_data['From']}, To: {email_data['To']}, Body: {email_data['Body']}"
                emails.append(email_data)
                # emails.append(email_data)
    
    # print(emails)
    return emails


def call_googlesheets(input_text="Test"):
    """
    Makes a POST request to the googlesheets endpoint
    Args:
        input_text: Text to send in the request (defaults to "Test")
    Returns:
        The response from the API
    """
    # url = "https://crmai-221518599345.us-central1.run.app/googlesheets"
    url="https://63f5-199-94-1-204.ngrok-free.app/googlesheets"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "input": input_text
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
        return response.json()
    except Exception as e:
        print(f"Error calling googlesheets API: {e}")
        return {"error": str(e)}

# Run our application
if __name__ == "__main__":
    # app.run(port=5002)
    
    # test_email = "ID: 19470faafdfa3669, Subject: Call Yesterday :), Snippet: Hello Eshan, Great conversation yesterday! Excited that you are ready to buy $1m dollars worth of products. Will be fun to see you in Florida next week. Bill, From: [{'name': 'Newman, Bill', 'email': 'bnewman@mba2026.hbs.edu'}], To: [{'name': 'Eshan Tarneja', 'email': 'eshantarneja@gmail.com'}], Body: Hello Eshan, \n\nGreat conversation yesterday! Excited that you are ready to buy $1m dollars worth of products. Will be fun to see you in Florida next week. \n\nBill\n\n"
    # result = call_googlesheets(test_email)
    # print("result:", result)
    emails=get_emails_recent(1)
    for email in emails:
        print("type of email: ", type(email))
        print("------------------------------------------------")
        print("email: ", email)
        print("------------------------------------------------")
        result = call_googlesheets(email)
        print("result:", result)

    # result = call_googlesheets("Test")
    # print(result)

