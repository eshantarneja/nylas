# Import your dependencies
from dotenv import load_dotenv
import os
from nylas import Client
from flask import Flask, request, redirect, url_for, session, jsonify
from flask_session.__init__ import Session
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest

# Load your env variables
load_dotenv()

    
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
                "ID": "",
                "Subject": "",
                "Snippet": "",
                "From": "",
                "To": "",
                    "Body": ""
                }
                email_data["ID"] = msg.id
                email_data["Subject"] = msg.subject
                email_data["Snippet"] = msg.snippet
                email_data["From"] = msg.from_
                email_data["To"] = msg.to
                # email_data["Body"] = msg.body
                emails.append(email_data)
    
    return emails

# Run our application
if __name__ == "__main__":
    # app.run(port=5002)
    print(get_emails_recent(3))

