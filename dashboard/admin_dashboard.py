
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# --------------------------------------------------
# Project Paths and Imports
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# Allow direct Streamlit execution from the project root.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from escalation.escalation_manager import (
    get_escalation_status,
    get_escalation_history,
    record_escalation_action,
)

LOG_FILE = BASE_DIR / "logs" / "support_logs.csv"

EXPECTED_COLUMNS = [
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
    "policy_sources",
]


# --------------------------------------------------
# Load Support Logs
# --------------------------------------------------

def load_support_logs():
    """Load and normalize customer support records."""

    if not LOG_FILE.exists():
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    try:
        df = pd.read_csv(
            LOG_FILE,
            encoding="utf-8-sig",
            dtype={"ticket_id": str},
        )

    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    for column in EXPECTED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True,
    )

    df["escalation_required"] = (
        df["escalation_required"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )

    for column in [
        "category",
        "urgency",
        "sentiment",
        "resolution_status",
    ]:
        df[column] = (
            df[column]
            .fillna("unknown")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    for column in [
        "complaint",
        "summary",
        "customer_response",
        "escalation_reason",
        "policy_sources",
    ]:
        df[column] = df[column].fillna("")

    return df


# --------------------------------------------------
# Human Review Status
# --------------------------------------------------

def add_human_review_status(df):
    """Attach current human review state to each ticket."""

    df = df.copy()

    statuses = []
    agents = []

    for _, ticket in df.iterrows():
        if not ticket["escalation_required"]:
            statuses.append("not_required")
            agents.append("")
            continue

        review = get_escalation_status(
            str(ticket["ticket_id"])
        )

        if review:
            statuses.append(
                review.get("status", "pending_review")
            )
            agents.append(
                review.get("agent_name", "")
            )
        else:
            statuses.append("pending_review")
            agents.append("")

    df["human_review_status"] = statuses
    df["assigned_agent"] = agents

    return df


# --------------------------------------------------
# Admin Dashboard
# --------------------------------------------------

def render_admin_dashboard():

    st.title("📊 SupportIQ AI — Admin Dashboard")

    st.caption(
        "Support operations, ticket analytics, "
        "and human escalation management"
    )

    if st.button("🔄 Refresh Dashboard"):
        st.rerun()

    df = load_support_logs()

    if df.empty:
        st.info(
            "No support tickets found yet. "
            "Submit a customer complaint first."
        )
        return

    df = add_human_review_status(df)

    st.divider()

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------

    st.subheader("Filter Tickets")

    col1, col2, col3 = st.columns(3)

    with col1:
        category_filter = st.multiselect(
            "Category",
            sorted(df["category"].unique().tolist()),
            default=sorted(
                df["category"].unique().tolist()
            ),
        )

    with col2:
        urgency_filter = st.multiselect(
            "Urgency",
            sorted(df["urgency"].unique().tolist()),
            default=sorted(
                df["urgency"].unique().tolist()
            ),
        )

    with col3:
        status_filter = st.multiselect(
            "AI Resolution Status",
            sorted(
                df["resolution_status"].unique().tolist()
            ),
            default=sorted(
                df["resolution_status"].unique().tolist()
            ),
        )

    filtered_df = df[
        df["category"].isin(category_filter)
        & df["urgency"].isin(urgency_filter)
        & df["resolution_status"].isin(status_filter)
    ].copy()

    st.divider()

    # --------------------------------------------------
    # KPI Metrics
    # --------------------------------------------------

    total_tickets = len(filtered_df)

    escalations = int(
        filtered_df["escalation_required"].sum()
    )

    resolved = int(
        (
            (filtered_df["resolution_status"] == "resolved")
            & (~filtered_df["escalation_required"])
        ).sum()
        +
        (
            filtered_df["human_review_status"] == "resolved"
        ).sum()
    )

    pending = int(
        (
            filtered_df["resolution_status"]
            == "pending_customer_action"
        ).sum()
    )

    active_escalations = int(
        (
            filtered_df["escalation_required"]
            & (
                filtered_df["human_review_status"]
                != "resolved"
            )
        ).sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🎫 Total Tickets", total_tickets)
    col2.metric("🚨 Total Escalations", escalations)
    col3.metric("✅ Resolved", resolved)
    col4.metric("⏳ Pending Customer", pending)

    st.metric(
        "🔔 Active Human Escalations",
        active_escalations
    )

    st.divider()

    # --------------------------------------------------
    # Analytics Charts
    # --------------------------------------------------

    st.subheader("Support Analytics")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Tickets by Category")

        category_counts = (
            filtered_df["category"]
            .value_counts()
            .rename_axis("Category")
            .to_frame("Tickets")
        )

        st.bar_chart(category_counts)

    with right:
        st.markdown("#### Tickets by Urgency")

        urgency_counts = (
            filtered_df["urgency"]
            .value_counts()
            .rename_axis("Urgency")
            .to_frame("Tickets")
        )

        st.bar_chart(urgency_counts)

    left, right = st.columns(2)

    with left:
        st.markdown("#### AI Resolution Status")

        status_counts = (
            filtered_df["resolution_status"]
            .value_counts()
            .rename_axis("Status")
            .to_frame("Tickets")
        )

        st.bar_chart(status_counts)

    with right:
        st.markdown("#### Customer Sentiment")

        sentiment_counts = (
            filtered_df["sentiment"]
            .value_counts()
            .rename_axis("Sentiment")
            .to_frame("Tickets")
        )

        st.bar_chart(sentiment_counts)

    st.divider()

    # --------------------------------------------------
    # Human Escalation Queue
    # --------------------------------------------------

    st.subheader("🚨 Human Escalation Queue")

    escalated_df = filtered_df[
        filtered_df["escalation_required"]
    ].copy()

    if escalated_df.empty:
        st.success(
            "No escalated cases match the current filters."
        )
    else:
        active_queue = escalated_df[
            escalated_df["human_review_status"]
            != "resolved"
        ]

        if active_queue.empty:
            st.success(
                "All escalated cases have completed "
                "human review."
            )
        else:
            st.warning(
                f"{len(active_queue)} case(s) "
                "require human attention."
            )

        st.dataframe(
            escalated_df[
                [
                    "ticket_id",
                    "timestamp",
                    "category",
                    "urgency",
                    "human_review_status",
                    "assigned_agent",
                    "summary",
                    "escalation_reason",
                ]
            ].sort_values(
                "timestamp",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Escalations are recorded locally. "
        "No external helpdesk notification is sent."
    )

    st.divider()

    # --------------------------------------------------
    # Ticket History
    # --------------------------------------------------

    st.subheader("📋 Customer Support History")

    display_columns = [
        "ticket_id",
        "timestamp",
        "category",
        "urgency",
        "sentiment",
        "resolution_status",
        "human_review_status",
        "assigned_agent",
        "escalation_required",
        "policy_sources",
    ]

    st.dataframe(
        filtered_df[display_columns].sort_values(
            "timestamp",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------
    # Inspect Ticket
    # --------------------------------------------------

    st.subheader("🔎 Inspect Ticket")

    if not filtered_df.empty:

        ticket_ids = (
            filtered_df["ticket_id"]
            .dropna()
            .astype(str)
            .tolist()
        )

        selected_ticket = st.selectbox(
            "Select Ticket ID",
            ticket_ids,
        )

        selected_rows = filtered_df[
            filtered_df["ticket_id"]
            == selected_ticket
        ]

        if not selected_rows.empty:

            ticket = selected_rows.iloc[0]

            with st.expander(
                "View Full Ticket Details",
                expanded=True,
            ):

                st.write(
                    "**Customer Complaint:**",
                    ticket["complaint"],
                )

                st.write(
                    "**AI Response:**",
                    ticket["customer_response"],
                )

                st.write(
                    "**AI Resolution Status:**",
                    ticket["resolution_status"],
                )

                st.write(
                    "**Human Review Status:**",
                    ticket["human_review_status"],
                )

                st.write(
                    "**Assigned Agent:**",
                    ticket["assigned_agent"]
                    or "Not assigned",
                )

                st.write(
                    "**Escalation Reason:**",
                    ticket["escalation_reason"],
                )

                st.write(
                    "**Policy Sources:**",
                    ticket["policy_sources"],
                )

    # --------------------------------------------------
    # Human Escalation Management
    # --------------------------------------------------

    st.divider()

    st.subheader("👨‍💻 Human Escalation Management")

    all_escalated = df[
        df["escalation_required"]
    ].copy()

    if all_escalated.empty:

        st.info(
            "No tickets require human review."
        )

    else:

        ticket_options = (
            all_escalated
            .sort_values("timestamp", ascending=False)
            ["ticket_id"]
            .dropna()
            .astype(str)
            .tolist()
        )

        review_ticket = st.selectbox(
            "Select Escalated Ticket",
            ticket_options,
            key="review_ticket",
        )

        current = get_escalation_status(
            review_ticket
        )

        if current:

            status = current["status"]
            assigned_agent = current["agent_name"]

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Ticket ID:**")
                st.code(review_ticket)

            with col2:
                st.write("**Human Review Status:**")
                st.info(
                    status.replace("_", " ").title()
                )

            st.write(
                "**Assigned Agent:**",
                assigned_agent or "Not assigned",
            )

            if status == "resolved":

                st.success(
                    "This case has been resolved "
                    "by the human support agent."
                )

            else:

                if status == "pending_review":
                    action = "assign"
                    button_label = "Assign Ticket"

                elif status == "assigned":
                    action = "start_progress"
                    button_label = "Start Investigation"

                elif status == "in_progress":
                    action = "resolve"
                    button_label = "Resolve Case"

                else:
                    action = None
                    button_label = "Unknown Action"

                if action:

                    with st.form(
                        key=f"human_review_{review_ticket}"
                    ):

                        if status == "pending_review":

                            agent_name = st.text_input(
                                "Human Agent Name",
                                placeholder="Support Agent 1",
                            )

                        else:

                            agent_name = assigned_agent

                            st.text_input(
                                "Assigned Agent",
                                value=assigned_agent,
                                disabled=True,
                            )

                        notes = st.text_area(
                            "Action Notes",
                            placeholder=(
                                "Describe the investigation "
                                "or resolution outcome."
                            ),
                        )

                        submitted = st.form_submit_button(
                            button_label,
                            type="primary",
                        )

                    if submitted:

                        try:

                            record = record_escalation_action(
                                ticket_id=review_ticket,
                                action=action,
                                agent_name=agent_name,
                                notes=notes,
                            )

                            st.success(
                                "Action saved: "
                                + record["status"]
                            )

                            st.rerun()

                        except ValueError as error:
                            st.error(str(error))

            with st.expander(
                "📜 View Human Action History"
            ):

                history = get_escalation_history(
                    review_ticket
                )

                if history:

                    history_df = pd.DataFrame(
                        history
                    )

                    st.dataframe(
                        history_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "No human actions recorded yet."
                    )

    # --------------------------------------------------
    # CSV Export
    # --------------------------------------------------

    st.divider()

    st.subheader("📥 Export Support Records")

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Download Filtered CSV",
        data=csv_data,
        file_name="supportiq_support_report.csv",
        mime="text/csv",
        use_container_width=True,
    )


# --------------------------------------------------
# Application Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    st.set_page_config(
        page_title="SupportIQ Admin Dashboard",
        page_icon="📊",
        layout="wide",
    )

    render_admin_dashboard()
