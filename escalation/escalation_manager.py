
import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SUPPORT_LOG = BASE_DIR / "logs" / "support_logs.csv"
ESCALATION_LOG = BASE_DIR / "logs" / "escalation_actions.csv"

ACTION_FIELDS = [
    "action_id",
    "ticket_id",
    "timestamp",
    "action",
    "agent_name",
    "status",
    "notes",
]

VALID_STATUSES = {
    "pending_review",
    "assigned",
    "in_progress",
    "resolved",
}


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )


def get_support_ticket(ticket_id):
    """Find an existing support ticket."""

    if not SUPPORT_LOG.exists():
        return None

    with SUPPORT_LOG.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row.get("ticket_id") == ticket_id:
                return row

    return None


def is_escalated_ticket(ticket):
    """Check the original AI escalation decision."""

    if not ticket:
        return False

    return str(
        ticket.get("escalation_required", "")
    ).strip().lower() in {"true", "1", "yes"}


def get_escalation_history(ticket_id):
    """Return all recorded human actions for a ticket."""

    if not ESCALATION_LOG.exists():
        return []

    with ESCALATION_LOG.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        return [
            row for row in csv.DictReader(file)
            if row.get("ticket_id") == ticket_id
        ]


def get_escalation_status(ticket_id):
    """Return the current human review status."""

    history = get_escalation_history(ticket_id)

    if history:
        latest = history[-1]
        return {
            "ticket_id": ticket_id,
            "status": latest["status"],
            "agent_name": latest["agent_name"],
            "last_action": latest["action"],
            "updated_at": latest["timestamp"],
        }

    ticket = get_support_ticket(ticket_id)

    if not is_escalated_ticket(ticket):
        return None

    return {
        "ticket_id": ticket_id,
        "status": "pending_review",
        "agent_name": "",
        "last_action": "",
        "updated_at": "",
    }


def record_escalation_action(
    ticket_id,
    action,
    agent_name,
    notes="",
):
    """
    Append a human review action to the audit log.

    Supported actions:
      assign
      start_progress
      resolve
    """

    ticket_id = str(ticket_id).strip()
    agent_name = str(agent_name).strip()
    notes = str(notes).strip()
    action = str(action).strip().lower()

    ticket = get_support_ticket(ticket_id)

    if ticket is None:
        raise ValueError(
            f"Ticket {ticket_id} does not exist."
        )

    if not is_escalated_ticket(ticket):
        raise ValueError(
            "Only escalated tickets can enter "
            "the human review workflow."
        )

    if not agent_name:
        raise ValueError("Agent name is required.")

    current = get_escalation_status(ticket_id)
    current_status = current["status"]

    transitions = {
        "pending_review": {
            "assign": "assigned",
        },
        "assigned": {
            "start_progress": "in_progress",
        },
        "in_progress": {
            "resolve": "resolved",
        },
        "resolved": {},
    }

    next_status = transitions.get(
        current_status, {}
    ).get(action)

    if next_status is None:
        raise ValueError(
            f"Cannot perform '{action}' "
            f"when ticket status is '{current_status}'."
        )

    # After assignment, the same agent must perform
    # subsequent actions.
    assigned_agent = current.get("agent_name", "")

    if (
        current_status != "pending_review"
        and agent_name != assigned_agent
    ):
        raise ValueError(
            "Only the assigned agent can update "
            "this ticket."
        )

    if action == "resolve" and not notes:
        raise ValueError(
            "Resolution notes are required."
        )

    ESCALATION_LOG.parent.mkdir(
        parents=True, exist_ok=True
    )

    needs_header = (
        not ESCALATION_LOG.exists()
        or ESCALATION_LOG.stat().st_size == 0
    )

    record = {
        "action_id": "ACT-" + uuid.uuid4().hex[:10].upper(),
        "ticket_id": ticket_id,
        "timestamp": utc_timestamp(),
        "action": action,
        "agent_name": agent_name,
        "status": next_status,
        "notes": notes,
    }

    with ESCALATION_LOG.open(
        "a", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=ACTION_FIELDS
        )

        if needs_header:
            writer.writeheader()

        writer.writerow(record)

    return record


def main():
    print("=" * 60)
    print("SupportIQ AI - Human Escalation Manager")
    print("=" * 60)

    ticket_id = input(
        "\nEnter escalated Ticket ID: "
    ).strip()

    current = get_escalation_status(ticket_id)

    if current is None:
        print(
            "Ticket not found or not eligible "
            "for human escalation."
        )
        return

    print("\nCurrent escalation status:")
    print(json.dumps(current, indent=4))

    print("\nAvailable Actions:")
    print("1. Assign to Agent")
    print("2. Start Progress")
    print("3. Resolve Case")
    print("4. View Action History")

    choice = input("\nSelect action (1-4): ").strip()

    if choice == "4":
        history = get_escalation_history(ticket_id)
        print(json.dumps(history, indent=4))
        return

    actions = {
        "1": "assign",
        "2": "start_progress",
        "3": "resolve",
    }

    action = actions.get(choice)

    if action is None:
        print("Invalid action.")
        return

    agent_name = input(
        "Enter human agent name: "
    ).strip()

    notes = input(
        "Enter action notes: "
    ).strip()

    try:
        result = record_escalation_action(
            ticket_id=ticket_id,
            action=action,
            agent_name=agent_name,
            notes=notes,
        )

        print("\nAction recorded successfully!")
        print(json.dumps(result, indent=4))

    except ValueError as error:
        print(f"\nAction rejected: {error}")


if __name__ == "__main__":
    main()
