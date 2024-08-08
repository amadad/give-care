import json
import os
from flask import Flask, request, render_template
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from typing import Optional
from pydantic import BaseModel
from demo_util import color, function_to_schema
from openai import AzureOpenAI

app = Flask(__name__)

# Twilio configuration
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = '+18889668985'

twilioclient = Client(account_sid, auth_token)

# Azure OpenAI configuration
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment_name = 'gpt-4o-mini-care'

# Define Agent and Response classes using Pydantic
class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini-care"
    instructions: str = "You are a helpful Agent"
    tools: list = []

class Response(BaseModel):
    agent: Optional[Agent]
    messages: list

# ===== Agents =====

def escalate_to_human(summary):
    """Only call this if explicitly asked to."""
    return "Escalating to human agent. Summary: " + summary

def transfer_to_sales_agent():
    """Use for anything sales or buying related."""
    return sales_agent

def transfer_to_issues_and_repairs():
    """Use for issues, repairs, or refunds."""
    return issues_and_repairs_agent

def transfer_back_to_triage():
    """Call this if the user brings up a topic outside of your purview,
    including escalating to human."""
    return triage_agent

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "You are a customer service bot for ACME Inc. "
        "Introduce yourself. Always be very brief. "
        "Gather information to direct the customer to the right department. "
        "But make your questions subtle and natural."
    ),
    tools=[transfer_to_sales_agent, transfer_to_issues_and_repairs, escalate_to_human],
)

sales_agent = Agent(
    name="Sales Agent",
    instructions=(
        "You are a sales agent for ACME Inc."
        "Always answer in a sentence or less."
        "Follow the following routine with the user:"
        "1. Ask them about any problems in their life related to catching roadrunners.\n"
        "2. Casually mention one of ACME's crazy made-up products can help.\n"
        " - Don't mention price.\n"
        "3. Once the user is bought in, drop a ridiculous price.\n"
        "4. Only after everything, and if the user says yes, "
        "tell them a crazy caveat and execute their order.\n"
    ),
    tools=[transfer_back_to_triage],
)

issues_and_repairs_agent = Agent(
    name="Issues and Repairs Agent",
    instructions=(
        "You are a customer support agent for ACME Inc."
        "Always answer in a sentence or less."
        "Follow the following routine with the user:"
        "1. First, ask probing questions and understand the user's problem deeper.\n"
        " - unless the user has already provided a reason.\n"
        "2. Propose a fix (make one up).\n"
        "3. ONLY if not satisfied, offer a refund.\n"
        "4. If accepted, search for the ID and then execute refund."
    ),
    tools=[transfer_back_to_triage],
)

# Define the runtime function for processing messages
def run_full_turn(agent, messages):
    current_agent = agent
    num_init_messages = len(messages)
    messages = messages.copy()

    while True:
        tool_schemas = [function_to_schema(tool) for tool in current_agent.tools]
        tools = {tool.__name__: tool for tool in current_agent.tools}

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "system", "content": current_agent.instructions}] + messages,
            tools=tool_schemas or None,
        )
        message = response.choices[0].message
        messages.append(message)

        if message.content:
            print(color(f"{current_agent.name}:", "yellow"), message.content)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tools, current_agent.name)

            if type(result) is Agent:
                current_agent = result
                result = f"Transferred to {current_agent.name}. Adopt persona immediately."

            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(result_message)

    return Response(agent=current_agent, messages=messages[num_init_messages:])

def execute_tool_call(tool_call, tools, agent_name):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    return tools[name](**args)

# Flask route to handle incoming SMS
@app.route('/sms', methods=['POST'])
def sms_reply():
    incoming_message = request.form['Body']
    messages = [{"role": "user", "content": incoming_message}]

    # Initialize agent (starting with the triage agent)
    agent = triage_agent

    # Run the full turn with the received message
    response = run_full_turn(agent, messages)

    # Prepare the response
    reply_message = response.messages[-1].content if response.messages else "Something went wrong."

    # Create a Twilio response object
    resp = MessagingResponse()
    resp.message(reply_message)

    return str(resp)

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)