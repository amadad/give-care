import os
import psycopg2
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from phi.assistant import Assistant, AssistantMemory
from phi.llm.azure import AzureOpenAIChat
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.llm.message import Message
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = Flask(__name__)

# Twilio setup
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'), 
    os.getenv('TWILIO_AUTH_TOKEN')
)

# Azure OpenAI setup
llm = AzureOpenAIChat(
    model="gpt-4o-mini-care",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Database setup with psycopg2
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://", 1)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create a storage backend using the Postgres database
storage = PgAssistantStorage(
    table_name="test_users",  
    db_url=DATABASE_URL,
)

# Simplified Pydantic Model
class User(BaseModel):
    id: Optional[int] = Field(None, description="Primary key, auto-incremented identifier for each user.")
    phone_number: str = Field(..., max_length=15, description="Phone number of the user, serves as a unique contact method.")
    created_at: datetime = Field(..., description="Timestamp indicating when the user's record was created.")
    loved_one_name: Optional[str] = Field(None, max_length=100, description="Name of the loved one the user is caring for.")
    loved_one_condition: Optional[str] = Field(None, max_length=255, description="Health condition or status of the loved one.")

# Assistant setup
assistant = Assistant(
    llm=llm,
    user_id=None,
    storage=storage,
    memory=AssistantMemory(),  
    add_chat_history_to_messages=True,  
    add_chat_history_to_prompt=False,  
    num_history_messages=6,  
    create_memories=True,  
    update_memory_after_run=True,  
    description="This is a care assistant for users to manage their loved ones.",
    name="Care Assistant",
    run_id=None,
    instructions=[
        "You're a caregiving assistant here to help manage the care of loved ones.",
        "1. Greet new users warmly and ask for the name of their loved one.",
        "2. Ask about their loved one's condition.",
        "3. Confirm information before saving it.",
        "4. For returning users, ask follow-up questions based on past interactions.",
        "Keep responses under 160 characters. Use friendly and supportive language. Split longer messages into no more than two texts."
    ],
)

@app.route('/sms', methods=['POST'])
def sms_reply():
    incoming_msg = request.form.get('Body')
    sender_phone_number = request.form.get('From')
    resp = MessagingResponse()

    # Check if the user exists in the database
    cur.execute("SELECT id, loved_one_name, loved_one_condition FROM test_users WHERE phone_number = %s", (sender_phone_number,))
    user = cur.fetchone()

    if user:
        user_id, loved_one_name, loved_one_condition = user

        if not loved_one_name:
            # Store the loved one's name and ask for their condition
            cur.execute("UPDATE test_users SET loved_one_name = %s WHERE id = %s", (incoming_msg, user_id))
            conn.commit()
            assistant_response = "Thanks! What is their condition?"
        elif not loved_one_condition:
            # Store the loved one's condition and engage in a conversation
            cur.execute("UPDATE test_users SET loved_one_condition = %s WHERE id = %s", (incoming_msg, user_id))
            conn.commit()
            assistant_response = f"Thank you. I see your loved one is dealing with {incoming_msg}. How are you managing, and what's been most challenging?"
        else:
            # Engage in context-aware conversation based on user input
            if "tell me about" in incoming_msg.lower() or "explain" in incoming_msg.lower():
                assistant_response = f"{loved_one_condition} can present unique challenges. What specific concerns do you have about managing {loved_one_name}'s care?"
            else:
                assistant_response = f"How can I assist you today with {loved_one_name}'s {loved_one_condition}?"

    else:
        # If new user, greet and ask for loved one's name
        cur.execute(
            "INSERT INTO test_users (phone_number, created_at) VALUES (%s, %s) RETURNING id",
            (sender_phone_number, datetime.now())
        )
        new_user_id = cur.fetchone()[0]
        conn.commit()
        assistant_response = "🫶🏽 Welcome to GiveCare! I'm Mira, your caregiving assistant. I'm here to help. What is the name of your loved one?"

    # Send the response back via SMS
    resp.message(assistant_response)
    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)