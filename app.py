
import asyncio
import streamlit as st

from team import process_complaint


# ==========================================
# Page Configuration
# ==========================================

st.set_page_config(
    page_title="SupportIQ AI",
    page_icon="🎧",
    layout="wide"
)


# ==========================================
# Conversation Memory
# ==========================================

if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []

if "support_result" not in st.session_state:
    st.session_state["support_result"] = None


# ==========================================
# Custom Styling
# ==========================================

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

.main-title {
    font-size: 2.5rem;
    font-weight: 750;
    margin-bottom: 0.25rem;
}

.subtitle {
    color: #888;
    margin-bottom: 1.5rem;
}

.ticket-box {
    padding: 12px 16px;
    border: 1px solid rgba(128, 128, 128, 0.3);
    border-radius: 10px;
    margin-top: 8px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# Header
# ==========================================

st.markdown(
    '<div class="main-title">🎧 SupportIQ AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Intelligent Multi-Agent Customer Support Portal'
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# Sidebar
# ==========================================

with st.sidebar:

    st.header("SupportIQ AI")
    st.caption("AutoGen + FAISS Vector RAG")

    st.divider()

    st.subheader("AI Workflow")

    st.write("1. Customer Query Agent")
    st.write("2. Knowledge Agent")
    st.write("3. Resolution Agent")
    st.write("4. Log Agent")

    st.divider()

    st.subheader("Conversation Memory")

    message_count = len(
        st.session_state["conversation_history"]
    )

    st.caption(
        f"Messages in current session: {message_count}"
    )

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True
    ):
        st.session_state["conversation_history"] = []
        st.session_state["support_result"] = None
        st.session_state["customer_complaint"] = ""
        st.rerun()

    st.divider()

    st.info(
        "Customer complaints are classified automatically. "
        "Responses are grounded in the company knowledge base."
    )


# ==========================================
# Customer Complaint Form
# ==========================================

st.subheader("How can we help you?")

complaint = st.text_area(
    "Describe your issue",
    height=140,
    placeholder=(
        "Example: My order is delayed. "
        "When will it arrive?"
    ),
    key="customer_complaint"
)

submitted = st.button(
    "✨ Analyze & Resolve",
    type="primary",
    use_container_width=True
)


# ==========================================
# Process Customer Complaint
# ==========================================

if submitted:

    current_complaint = complaint.strip()

    if not current_complaint:

        st.warning(
            "Please enter your complaint."
        )

    else:

        previous_history = list(
            st.session_state["conversation_history"]
        )

        result = None

        with st.spinner(
            "Our AI agents are analyzing your request..."
        ):

            try:

                result = asyncio.run(
                    process_complaint(
                        complaint=current_complaint,
                        conversation_history=previous_history
                    )
                )

            except Exception:

                st.error(
                    "Unable to process your request. "
                    "Please try again or contact support."
                )

        # Update session state only after the
        # complete workflow succeeds.
        if result is not None:

            customer_response = str(
                result["resolution"].get(
                    "customer_response",
                    "No response generated."
                )
            )

            st.session_state["support_result"] = result

            st.session_state[
                "conversation_history"
            ].append({
                "role": "user",
                "content": current_complaint
            })

            st.session_state[
                "conversation_history"
            ].append({
                "role": "assistant",
                "content": customer_response
            })

            # Refresh the sidebar message count
            # and conversation history immediately.
            st.rerun()


# ==========================================
# Conversation History Display
# ==========================================

history = st.session_state["conversation_history"]

if history:

    st.divider()

    st.subheader("💬 Conversation History")

    with st.container(height=300):

        for message in history:

            role = message.get("role", "assistant")
            content = message.get("content", "")

            with st.chat_message(role):
                st.write(content)


# ==========================================
# Display Customer Support Result
# ==========================================

result = st.session_state.get("support_result")

if result:

    query = result["query_analysis"]
    knowledge = result["knowledge_analysis"]
    resolution = result["resolution"]

    st.divider()

    st.subheader("AI Support Response")

    customer_response = resolution.get(
        "customer_response",
        "No response generated."
    )

    st.success(customer_response)

    # ------------------------------------------
    # Ticket ID
    # ------------------------------------------

    st.markdown("#### 🎫 Your Support Ticket")

    ticket_id = result.get(
        "ticket_id", "N/A"
    )

    st.code(
        ticket_id,
        language=None
    )

    st.caption(
        "Please save your ticket ID for reference."
    )

    # ------------------------------------------
    # Classification Metrics
    # ------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Category",
        str(query.get("category") or "other").title()
    )

    col2.metric(
        "Urgency",
        str(query.get("urgency") or "medium").title()
    )

    col3.metric(
        "Sentiment",
        str(query.get("sentiment") or "neutral").title()
    )

    st.divider()

    # ------------------------------------------
    # Resolution Details
    # ------------------------------------------

    left, right = st.columns(2)

    with left:

        st.subheader("Resolution Details")

        status = str(
            resolution.get("resolution_status") or "unknown"
        )

        st.write(
            "**Status:**",
            status.replace("_", " ").title()
        )

        if resolution.get("escalation_required"):

            st.warning(
                "This issue requires human support review."
            )

        else:

            st.success(
                "No human escalation required."
            )

        if resolution.get("escalation_reason"):

            st.write(
                "**Escalation Reason:**",
                resolution["escalation_reason"]
            )

    # ------------------------------------------
    # Knowledge Base Sources
    # ------------------------------------------

    with right:

        st.subheader("Knowledge Base")

        sources = resolution.get(
            "policy_sources", []
        )

        if sources:

            for source in sources:
                st.write(f"📄 {source}")

        else:

            st.info(
                "No matching policy source available."
            )

        st.write(
            "**Policy Evidence Sufficient:**",
            "Yes"
            if knowledge.get("sufficient_evidence")
            else "No"
        )

    # ------------------------------------------
    # Customer Information
    # ------------------------------------------

    st.divider()

    st.info(
        "SupportIQ AI provides guidance based on "
        "available company policies. "
        "It does not access live order or account data."
    )

    st.caption(
        "Ticket IDs refer to internal support records. "
        "Human escalation is handled through the "
        "SupportIQ AI Admin Dashboard."
    )
