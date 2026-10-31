
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.knowledge_agent import analyze_knowledge

load_dotenv(BASE_DIR / ".env")


RESOLUTION_AGENT_SYSTEM_MESSAGE = """
You are the Resolution Agent for SupportIQ Store.

Your job is to create helpful, professional customer
support responses based on verified policy evidence.

Rules:
1. Use only the supplied knowledge analysis.
2. Never invent delivery dates, order statuses, refund
   approvals, customer records, or company policies.
3. Do not claim to have checked a live order or account.
4. Do not claim that a support ticket has been created.
5. If escalation is required, clearly explain that
   the issue needs human support review.
6. For security incidents, prioritize account safety.
7. Never request passwords, OTPs, or payment credentials.
8. If evidence is insufficient, avoid unsupported answers.
9. Be empathetic, concise, and professional.
10. Return only valid JSON without Markdown formatting.

Return this JSON structure:
{
    "customer_response": "Customer-friendly response",
    "resolution_status": "resolved",
    "escalation_required": false,
    "escalation_reason": "",
    "policy_sources": ["shipping_policy.md"]
}

Allowed resolution_status values:
- resolved: Policy guidance fully addresses the request.
- pending_customer_action: Customer must take an action.
- escalated: Human review is required.
"""


def create_resolution_agent(model_client):
    return AssistantAgent(
        name="resolution_agent",
        model_client=model_client,
        system_message=RESOLUTION_AGENT_SYSTEM_MESSAGE
    )


async def generate_resolution(
    complaint: str,
    category: str,
    urgency: str = "medium"
):
    """Retrieve policy analysis and generate a response."""

    knowledge = await analyze_knowledge(
        complaint=complaint,
        category=category,
        urgency=urgency
    )

    model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0
    )

    agent = create_resolution_agent(model_client)

    task = (
        f"Customer complaint:\n{complaint}\n\n"
        f"Category: {category}\n"
        f"Urgency: {urgency}\n\n"
        "Knowledge Agent analysis:\n"
        f"{json.dumps(knowledge, ensure_ascii=False, indent=2)}\n\n"
        "Generate a policy-grounded customer response. "
        "Return the required JSON."
    )

    try:
        result = await agent.run(task=task)
        response = json.loads(result.messages[-1].content)

        # Enforce escalation outside the language model.
        must_escalate = (
            urgency.lower() == "high"
            or bool(knowledge.get("escalation_required"))
            or not bool(knowledge.get("sufficient_evidence"))
        )

        if must_escalate:
            response["escalation_required"] = True
            response["resolution_status"] = "escalated"

            if not response.get("escalation_reason"):
                response["escalation_reason"] = (
                    knowledge.get("reason")
                    or "Human support review is required."
                )

            customer_text = str(
                response.get("customer_response", "")
            )

            if not any(
                phrase in customer_text.lower()
                for phrase in (
                    "human support",
                    "support team",
                    "specialist",
                    "human review"
                )
            ):
                response["customer_response"] = (
                    customer_text.strip()
                    + " This issue requires review by our "
                    "human support team."
                ).strip()

        # Source list comes from actual retrieval, not the LLM.
        response["policy_sources"] = knowledge.get(
            "sources", []
        )

        return response

    finally:
        await model_client.close()


async def main():
    print("=" * 60)
    print("SupportIQ AI - AutoGen Resolution Agent")
    print("=" * 60)

    categories = {
        "1": "shipping",
        "2": "refund",
        "3": "account",
        "4": "product",
        "5": "billing"
    }

    print("\nAvailable Categories:")
    for number, category in categories.items():
        print(f"{number}. {category}")

    complaint = input(
        "\nEnter customer complaint: "
    ).strip()

    category_input = input(
        "Select category (1-5 or name): "
    ).strip().lower()

    category = categories.get(
        category_input, category_input
    )

    if category not in categories.values():
        print("Invalid category.")
        return

    urgency = input(
        "Enter urgency (low/medium/high): "
    ).strip().lower() or "medium"

    if urgency not in ("low", "medium", "high"):
        print("Invalid urgency.")
        return

    if not complaint:
        print("Customer complaint cannot be empty.")
        return

    try:
        resolution = await generate_resolution(
            complaint=complaint,
            category=category,
            urgency=urgency
        )

        print("\nResolution Agent Output:")
        print(
            json.dumps(
                resolution,
                indent=4,
                ensure_ascii=False
            )
        )

    except Exception as error:
        print(f"\nResolution Agent failed: {error}")


if __name__ == "__main__":
    asyncio.run(main())
