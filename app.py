
import asyncio
import streamlit as st

from team import process_complaint


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="SupportIQ AI",
    page_icon="🎧",
    layout="wide"
)


# --------------------------------------------------
# Custom Styling
# --------------------------------------------------

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


# --------------------------------------------------
# Header
# --------------------------------------------------

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


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

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

    st.info(
        "Customer complaints are classified automatically. "
        "Responses are grounded in the company knowledge base."
    )


# --------------------------------------------------
# Customer Complaint Form
# --------------------------------------------------

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


# --------------------------------------------------
# Process Customer Complaint
# --------------------------------------------------

if submitted:

    if not complaint.strip():

        st.warning(
            "Please enter your complaint."
        )

    else:

        # Clear previous result before a new request.
        st.session_state.pop(
            "support_result", None
        )

        with st.spinner(
            "Our AI agents are analyzing your request..."
        ):

            try:

                result = asyncio.run(
                    process_complaint(
                        complaint.strip()
                    )
                )

                st.session_state[
                    "support_result"
                ] = result

            except Exception:

                st.error(
                    "Unable to process your request. "
                    "Please try again or contact support."
                )


# --------------------------------------------------
# Display Customer Support Result
# --------------------------------------------------

if "support_result" in st.session_state:

    result = st.session_state["support_result"]

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

    # --------------------------------------------------
    # Ticket ID - Full Width Display
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Classification Metrics
    # --------------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Category",
        query.get(
            "category", "other"
        ).title()
    )

    col2.metric(
        "Urgency",
        query.get(
            "urgency", "medium"
        ).title()
    )

    col3.metric(
        "Sentiment",
        query.get(
            "sentiment", "neutral"
        ).title()
    )

    st.divider()

    # --------------------------------------------------
    # Resolution Details
    # --------------------------------------------------

    left, right = st.columns(2)

    with left:

        st.subheader("Resolution Details")

        status = resolution.get(
            "resolution_status",
            "unknown"
        )

        st.write(
            "**Status:**",
            status.replace(
                "_", " "
            ).title()
        )

        if resolution.get(
            "escalation_required"
        ):

            st.warning(
                "This issue requires human "
                "support review."
            )

        else:

            st.success(
                "No human escalation required."
            )

        if resolution.get(
            "escalation_reason"
        ):

            st.write(
                "**Escalation Reason:**",
                resolution[
                    "escalation_reason"
                ]
            )

    # --------------------------------------------------
    # Knowledge Base Sources
    # --------------------------------------------------

    with right:

        st.subheader(
            "Knowledge Base"
        )

        sources = resolution.get(
            "policy_sources", []
        )

        if sources:

            for source in sources:

                st.write(
                    f"📄 {source}"
                )

        else:

            st.info(
                "No matching policy "
                "source available."
            )

        st.write(
            "**Policy Evidence Sufficient:**",
            "Yes"
            if knowledge.get(
                "sufficient_evidence"
            )
            else "No"
        )

    # --------------------------------------------------
    # Customer Information
    # --------------------------------------------------

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
