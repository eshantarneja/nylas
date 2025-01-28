# Import your dependencies
from dotenv import load_dotenv
import os
from nylas import Client
from flask import Flask, request, redirect, url_for, session, jsonify
from flask_session.__init__ import Session
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest
from nylas.models.webhooks import WebhookTriggers
import requests
import hmac
import hashlib
from bs4 import BeautifulSoup
import re

# Load your env variables
load_dotenv()

# Debug: Print environment variables
print(f"NYLAS_CLIENT_ID: {os.environ.get('NYLAS_CLIENT_ID')}")
print(f"NYLAS_API_KEY: {os.environ.get('NYLAS_API_KEY')}")
print(f"NYLAS_API_URI: {os.environ.get('NYLAS_API_URI')}")
print(f"EMAIL: {os.environ.get('EMAIL')}")

# Create the app
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize Nylas client
nylas = Client(
    api_key = os.environ.get("NYLAS_API_KEY"),
    api_uri = os.environ.get("NYLAS_API_URI")
)

print("Initialized Nylas client: ", nylas)

# Cache to store processed email IDs
processed_email_ids = set()

# Call the authorization page   
@app.route("/oauth/exchange", methods=["GET"])
def authorized():
    print("Authorization exchange request received")
    if session.get("grant_id") is None:
        code = request.args.get("code")
        print(f"Authorization code received: {code}")
        try:
            exchangeRequest = CodeExchangeRequest({
                "redirect_uri": "http://localhost:5002/oauth/exchange",
                "code": code,
                "client_id": os.environ.get("NYLAS_CLIENT_ID")
            })
            exchange = nylas.auth.exchange_code_for_token(exchangeRequest)
            session["grant_id"] = exchange.grant_id
            print(f"Grant ID set to: {session['grant_id']}")
        except Exception as e:
            print(f"Error during authorization: {e}")
        return redirect(url_for("recent_emails"))

# Main page
@app.route("/nylas/auth", methods=["GET"])
def login():
    print("Login request received")
    session.clear()
    if session.get("grant_id") is None:
        config = URLForAuthenticationConfig({"client_id": os.environ.get("NYLAS_CLIENT_ID"), 
                                            "redirect_uri" : "http://localhost:5002/oauth/exchange"})
        url = nylas.auth.url_for_oauth2(config)
        print(f"Redirecting to: {url}")
        return redirect(url)
    else:
        print(f"Grant ID already exists: {session['grant_id']}")
        return f'{session["grant_id"]}'

@app.route("/nylas/recent-emails", methods=["GET"])
def recent_emails():
    print("Recent emails request received")
    query_params = {"limit": 5} 
    try:
        print(session["grant_id"])
        messages, _, _ = nylas.messages.list(session["grant_id"], query_params)
        print(f"Messages fetched: {messages}")
        return jsonify(messages)
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return f'{e}'
    
@app.route("/nylas/recent-emails-hardcoded", methods=["GET"])
def recent_emails_hardcoded():
    print("Recent emails request received")
    
    # Get the `count` parameter from the query string, default to 5 if not provided
    count = request.args.get("count", default=5, type=int)
    
    # Get the `grant_id` parameter from the query string
    grant_id = request.args.get("grant_id")
    
    # If no `grant_id` is provided, return an error response
    if not grant_id:
        return jsonify({"error": "Missing required parameter 'grant_id'"}), 400

    query_params = {"limit": count}
    emails = []
    
    try:
        # Fetch messages using the `grant_id` and `count` parameter
        messages = nylas.messages.list(grant_id, query_params)
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
                    email_data["Body"] = msg.body
                    emails.append(email_data)   
        print(emails)
        return emails
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/nylas/send-email", methods=["GET"])
def send_email():
    print("Send email request received")
    try:
        body = {"subject" : "Your Subject Here", 
                     "body":"Your Email Here",
                     "reply_to":[{"name": "Name", "email": os.environ.get("EMAIL")}],
                     "to":[{"name": "Name", "email": os.environ.get("EMAIL")}]}

        message = nylas.messages.send(session["grant_id"], request_body = body).data

        print(f"Email sent: {message}")
        return jsonify(message)
    except Exception as e:
        print(f"Error sending email: {e}")
        return f'{e}'

@app.route("/nylas/instagram", methods=["GET", "POST"])
def receive_instagram():


    request_data = {
        'method': request.method,
        'args': request.args.to_dict(),
        'headers': dict(request.headers),
        'path': request.path,
        'url': request.url,
        'body': request.get_data().decode('utf-8'),
        'form': request.form.to_dict(),
        'json': request.get_json(silent=True),
        'cookies': request.cookies.to_dict()
    }

    instaData = request_data['form'] 
    print("type of instaData: ", type(instaData))
    print('instaData: ', instaData)
    call_firebase(instaData)
    return jsonify(instaData)

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

def call_firebase(input_text="Test", route="instagram"):
    """
    Makes a POST request to the specified firebase endpoint
    Args:
        input_text: Text to send in the request (defaults to "Test")
        route: The route to use for the request (defaults to "instagram")
    Returns:
        The response from the API
    """
    print(f"calling firebase with input: {input_text} and route: {route}")
    url = f"https://48c7-199-94-1-204.ngrok-free.app/firebase/{route}"
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
        print(f"Error calling firebase API: {e}")
        return {"error": str(e)}

@app.route("/nylas/webhook", methods=["GET", "POST"])
def webhook():
    print("\n=== Webhook Request Received ===")
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    
    if request.method == "GET":
        # Handle webhook challenge verification
        challenge = request.args.get("challenge")
        if challenge:
            print(f"Challenge received: {challenge}")
            return challenge
        return "No challenge found", 400

    # Handle POST requests (actual webhook notifications)
    if request.method == "POST":
        try:
            # Get the raw data
            raw_data = request.get_data()
            print(f"Raw webhook data: {raw_data.decode('utf-8')}")
            
            # Process the webhook notification
            webhook_data = request.get_json()
            
            print("\n=== Email Notification ===")
            print(f"Trigger: {webhook_data.get('type')}")
            
            # Get the webhook ID for duplicate checking
            webhook_id = webhook_data.get('id')
            
            # Check if we've already processed this webhook
            if webhook_id in processed_email_ids:
                print("\n")
                print("*" * 50)
                print("🚫 DUPLICATE WEBHOOK DETECTED 🚫")
                print(f"Webhook ID: {webhook_id}")
                print(f"Subject: {webhook_data.get('data', {}).get('object', {}).get('subject')}")
                print(f"From: {webhook_data.get('data', {}).get('object', {}).get('from', [{}])[0].get('email', '')}")
                print("This webhook has already been processed and will be skipped")
                print("*" * 50)
                print("\n")
                return "Duplicate webhook skipped", 200
            
            # Add the webhook ID to our processed set
            processed_email_ids.add(webhook_id)
            print(f"\nAdded new webhook ID to processed set: {webhook_id}")
            print(f"Total unique webhooks processed: {len(processed_email_ids)}\n")
            
            # Extract email details in the same format as get_emails_recent
            data = webhook_data.get('data', {})
            msg = data.get('object', {})
            
            if msg:
                email_data = {
                    "id": "",
                    "subject": "",
                    "snippet": "",
                    "from": "",
                    "to": "",
                    "body": "",
                    "date": "",
                    "debug": "true"
                }
                
                email_data["id"] = msg.get('id')
                email_data["subject"] = msg.get('subject')
                email_data["snippet"] = msg.get('snippet')
                email_data["from"] = msg.get('from', [{}])[0].get('email', '')  # Extract email from the first 'from' entry
                email_data["to"] = [to.get('email', '') for to in msg.get('to', [])]  # Extract all 'to' emails
                email_data["body"] = clean_email(msg.get('body', ''))
                
                print("\n=== Processed Email Details ===")
                print(f"ID: {email_data['id']}")
                print(f"Subject: {email_data['subject']}")
                print(f"Snippet: {email_data['snippet']}")
                print(f"From: {email_data['from']}")
                print(f"To: {email_data['to']}")
                print(f"Clean Body: {email_data['body']}")
                print("==========================\n")

                call_firebase(email_data, "email")
            
            return "Webhook processed", 200
            
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return f"Error: {str(e)}", 500

    return "Method not allowed", 405

@app.route("/nylas/create-webhook", methods=["GET"])
def create_webhook():
    try:
        webhook_url = os.environ.get("WEBHOOK_URL")
        if not webhook_url:
            return jsonify({"error": "WEBHOOK_URL not configured in environment"}), 500

        email = os.environ.get("EMAIL")
        if not email:
            return jsonify({"error": "EMAIL not configured in environment"}), 500

        webhook = nylas.webhooks.create(
            request_body={
                "trigger_types": [
                    "message.created"
                ],
                "webhook_url": webhook_url,
                "description": "Email notifications webhook",
                "notification_email_address": email,
            }
        )
        
        print("Created webhook:", webhook)
        return jsonify({
            "message": "Webhook created successfully",
            "webhook_id": webhook.id if hasattr(webhook, 'id') else None,
            "webhook_url": webhook_url
        }), 200
        
    except Exception as e:
        print(f"Error creating webhook: {e}")
        return jsonify({"error": str(e)}), 500

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

# Run our application
if __name__ == "__main__":
    app.run(port=5002)

