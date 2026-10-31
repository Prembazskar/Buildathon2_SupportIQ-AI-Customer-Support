
import asyncio
import json
import os

from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()


QUERY_AGENT_SYSTEM_MESSAGE = """
You are the Customer Query Agent for SupportIQ Store.

Your responsibility is to analyze customer complaints.

Identify:
1. category: shipping, refund, account, product, billing, or other
2. urgency: low, medium, or high
3. sentiment: positive, neutral, or negative
4. summary: concise description of the customer's issue

Rules:
- Do not answer or resolve the complaint.
- Do not invent customer or order information.
- Classify based only on the customer's message.
- Use high urgency for suspected account compromise,
  security threats, or other critical incidents.
- If multiple categories are relevant, choose the primary one.
- Return ONLY a valid JSON object.
- Do not include Markdown formatting.

Expected JSON:
{
    "category": "shipping",
    "urgency": "medium",
    "sentiment": "negative",
    "summary": "Customer reports a delayed order."
}
"""


def create_query_agent(model_client):
    return AssistantAgent(
        name="customer_query_agent",
        model_client=model_client,
        system_message=QUERY_AGENT_SYSTEM_MESSAGE
    )


async def main():

    model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0
    )

    agent = create_query_agent(model_client)

    try:
        complaint = input(
            "Enter customer complaint: "
        ).strip()

        if not complaint:
            print("Please enter a customer complaint.")
            return

        result = await agent.run(
            task=complaint
        )

        response = result.messages[-1].content

        try:
            parsed = json.loads(response)
            print("\nCustomer Query Analysis:")
            print(json.dumps(parsed, indent=4))
        except (json.JSONDecodeError, TypeError):
            print("\nAgent response was not valid JSON:")
            print(response)

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
