import os
import openai
from flask import Flask, request, render_template
from twilio.rest import Client

app = Flask(__name__)

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = '+18889668985'
twilioclient = Client(account_sid, auth_token)

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_affirmation_openai():
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates positive affirmations."},
            {"role": "user", "content": "Generate a word of affirmation."}
        ],
        max_tokens=50
    )
    return response.choices[0].message['content'].strip()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send_affirmation', methods=['POST'])
def send_affirmation():
    recipient_number = request.form['phone_number']
    affirmation = generate_affirmation_openai() 

    try:
        message = twilioclient.messages.create(
            body=affirmation,
            from_=twilio_phone_number,
            to=recipient_number
        )
        return "Affirmation sent successfully!"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)