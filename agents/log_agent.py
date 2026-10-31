
import csv
import json
import uuid

from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "support_logs.csv"

LOG_FIELDS = [
    "ticket_id",
    "timestamp",
    "complaint",
    "category",
    "urgency",
    "sentiment",
    "summary",
    "customer_response",
    "resolution_status",
    "escalation_required",
    "escalation_reason",
    "policy_sources"
]


def log_support_case(
    complaint: str,
    query_analysis: dict,
    resolution: dict
):
    """
    Log a completed support interaction.

    Returns the generated ticket ID and log path.
    """

    if not complaint.strip():
        raise ValueError("Complaint cannot be empty.")

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    ticket_id = (
        "SIQ-" + uuid.uuid4().hex[:10].upper()
    )

    timestamp = datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    row = {
        "ticket_id": ticket_id,
        "timestamp": timestamp,
        "complaint": complaint,
        "category": query_analysis.get(
            "category", "other"
        ),
        "urgency": query_analysis.get(
            "urgency", "medium"
        ),
        "sentiment": query_analysis.get(
            "sentiment", "neutral"
        ),
        "summary": query_analysis.get(
            "summary", ""
        ),
        "customer_response": resolution.get(
            "customer_response", ""
        ),
        "resolution_status": resolution.get(
            "resolution_status", "pending_customer_action"
        ),
        "escalation_required": bool(
            resolution.get("escalation_required", False)
        ),
        "escalation_reason": resolution.get(
            "escalation_reason", ""
        ),
        "policy_sources": json.dumps(
            resolution.get("policy_sources", []),
            ensure_ascii=False
        )
    }

    file_exists = LOG_FILE.exists()
    needs_header = (
        not file_exists or LOG_FILE.stat().st_size == 0
    )

    # utf-8-sig supports Excel on Windows.
    with LOG_FILE.open(
        "a",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=LOG_FIELDS
        )

        if needs_header:
            writer.writeheader()

        writer.writerow(row)

    return {
        "ticket_id": ticket_id,
        "timestamp": timestamp,
        "log_file": str(LOG_FILE),
        "escalation_required": row["escalation_required"]
    }


def main():
    print("=" * 60)
    print("SupportIQ AI - Support Case Logging Test")
    print("=" * 60)

    complaint = (
        "Someone accessed my account without permission!"
    )

    query_analysis = {
        "category": "account",
        "urgency": "high",
        "sentiment": "negative",
        "summary": (
            "Customer reports unauthorized account access."
        )
    }

    resolution = {
        "customer_response": (
            "Please change your password immediately. "
            "This issue requires human security review."
        ),
        "resolution_status": "escalated",
        "escalation_required": True,
        "escalation_reason": (
            "Suspected unauthorized account access."
        ),
        "policy_sources": [
            "account_and_login.md"
        ]
    }

    result = log_support_case(
        complaint=complaint,
        query_analysis=query_analysis,
        resolution=resolution
    )

    print("\nSupport case logged successfully!")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
