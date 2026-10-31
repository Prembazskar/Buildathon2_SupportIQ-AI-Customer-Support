
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.query_agent import create_query_agent
from agents.knowledge_agent import analyze_knowledge
from agents.resolution_agent import create_resolution_agent
from agents.log_agent import log_support_case


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def parse_agent_json(raw_response):
    """Parse and validate a JSON agent response."""

    if not isinstance(raw_response, str):
        raise ValueError("Agent returned non-text content.")

    data = json.loads(raw_response)

    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object.")

    return data


async def process_complaint(complaint: str):
    """Execute the complete SupportIQ AI workflow."""

    if not complaint or not complaint.strip():
        raise ValueError("Customer complaint cannot be empty.")

    model_client = OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0
    )

    try:
        # STEP 1: Customer Query Agent
        query_agent = create_query_agent(model_client)

        query_result = await query_agent.run(
            task=complaint
        )

        query_analysis = parse_agent_json(
            query_result.messages[-1].content
        )

        category = query_analysis.get(
            "category", "other"
        ).lower()

        urgency = query_analysis.get(
            "urgency", "medium"
        ).lower()

        # STEP 2: Knowledge Agent + FAISS
        knowledge = await analyze_knowledge(
            complaint=complaint,
            category=category,
            urgency=urgency
        )

        # STEP 3: Resolution Agent
        resolution_agent = create_resolution_agent(
            model_client
        )

        resolution_task = (
            f"Customer complaint:\n{complaint}\n\n"
            f"Query Agent analysis:\n"
            f"{json.dumps(query_analysis, ensure_ascii=False)}\n\n"
            f"Knowledge Agent analysis:\n"
            f"{json.dumps(knowledge, ensure_ascii=False)}\n\n"
            "Generate the required JSON resolution."
        )

        resolution_result = await resolution_agent.run(
            task=resolution_task
        )

        resolution = parse_agent_json(
            resolution_result.messages[-1].content
        )

        # Enforce escalation rules deterministically.
        must_escalate = (
            urgency == "high"
            or bool(knowledge.get("escalation_required"))
            or not bool(knowledge.get("sufficient_evidence"))
        )

        if must_escalate:
            resolution["escalation_required"] = True
            resolution["resolution_status"] = "escalated"
            resolution["escalation_reason"] = (
                knowledge.get("reason")
                or "Human support review is required."
            )

            response_text = str(
                resolution.get("customer_response", "")
            ).strip()

            if not any(
                phrase in response_text.lower()
                for phrase in [
                    "human support",
                    "support team",
                    "human review",
                    "specialist"
                ]
            ):
                response_text += (
                    " This issue requires review "
                    "by our human support team."
                )

            resolution["customer_response"] = (
                response_text.strip()
            )

        # An order-tracking instruction is not a
        # confirmation that the order was delivered.
        if (
            category == "shipping"
            and not must_escalate
            and resolution.get("resolution_status") == "resolved"
        ):
            resolution["resolution_status"] = (
                "pending_customer_action"
            )

        # Preserve retrieved sources, not model-generated ones.
        resolution["policy_sources"] = knowledge.get(
            "sources", []
        )

        # STEP 4: Log Agent
        log_result = log_support_case(
            complaint=complaint,
            query_analysis=query_analysis,
            resolution=resolution
        )

        return {
            "ticket_id": log_result["ticket_id"],
            "query_analysis": query_analysis,
            "knowledge_analysis": knowledge,
            "resolution": resolution,
            "logged": True
        }

    finally:
        await model_client.close()


async def main():
    print("=" * 60)
    print("SupportIQ AI - Integrated Customer Support")
    print("=" * 60)

    complaint = input(
        "\nEnter customer complaint: "
    ).strip()

    try:
        result = await process_complaint(complaint)

        print("\n" + "=" * 60)
        print("CUSTOMER SUPPORT RESULT")
        print("=" * 60)

        print(f"\nTicket ID: {result['ticket_id']}")

        query = result["query_analysis"]
        resolution = result["resolution"]

        print(f"Category: {query.get('category')}")
        print(f"Urgency: {query.get('urgency')}")
        print(f"Sentiment: {query.get('sentiment')}")

        print("\nCustomer Response:")
        print(resolution.get("customer_response", ""))

        print(
            "\nResolution Status:",
            resolution.get("resolution_status")
        )

        print(
            "Escalation Required:",
            resolution.get("escalation_required")
        )

        print(
            "Policy Sources:",
            ", ".join(
                resolution.get("policy_sources", [])
            )
        )

        print("\nCase saved to CSV successfully.")

    except Exception as error:
        print(f"\nWorkflow failed: {error}")


if __name__ == "__main__":
    asyncio.run(main())
