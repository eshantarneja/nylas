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
        return redirect(url_for("login"))

# Main page
@app.route("/nylas/auth", methods=["GET"])
def login():
    print("Login request received")
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
    app.run(port=5002)

