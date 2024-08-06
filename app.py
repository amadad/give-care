import os
from openai import OpenAI
from flask import Flask, request, render_template
from twilio.rest import Client
import random

app = Flask(__name__)

# Twilio configuration
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = '+18889668985'

# Check if credentials are set
if not account_sid or not auth_token:
    raise ValueError("Twilio credentials are not set. Please check your environment variables.")
twilioclient = Client(account_sid, auth_token)

# OpenAI configuration
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Function to generate affirmation using OpenAI
def generate_affirmation_openai():
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates positive affirmations."},
            {"role": "user", "content": "Generate a word of affirmation."}
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

# Route for the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route for sending the affirmation
@app.route('/send_affirmation', methods=['POST'])
def send_affirmation():
    recipient_number = request.form['phone_number']
    
    # Choose to use OpenAI or predefined affirmations
    # affirmation = generate_affirmation()  # Use this line for predefined affirmations
    affirmation = generate_affirmation_openai()  # Use this line for OpenAI-generated affirmations

    try:
        message = twilioclient.messages.create(
            body=affirmation,
            from_=twilio_phone_number,
            to=recipient_number
        )
        return "Affirmation sent successfully!"
    except Exception as e:
        return str(e)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)