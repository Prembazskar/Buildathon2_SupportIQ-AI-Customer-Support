
# SupportIQ AI — Intelligent Multi-Agent Customer Support

SupportIQ AI is an AI-powered customer support automation platform built for the Buildathon.

It combines AutoGen multi-agent orchestration, FAISS-based Retrieval-Augmented Generation (RAG), human-in-the-loop escalation, and an administrative dashboard.

## Live Application

- Customer Portal: https://supportiq.pbazskar.tech
- Admin Dashboard: https://supportiq-admin.pbazskar.tech (authentication required)

## Problem Statement

Traditional customer support workflows can suffer from slow response times, repetitive questions, inconsistent answers, and inefficient escalation.

SupportIQ AI addresses these challenges by automating customer query classification, policy retrieval, response generation, ticket logging, and human escalation.

## Key Features

- Multi-agent customer support automation
- AI-based query classification
- Urgency and sentiment detection
- FAISS vector search over support knowledge documents
- Policy-grounded response generation
- Automatic ticket creation and CSV logging
- Human-in-the-loop escalation
- Escalation assignment and resolution tracking
- Admin dashboard with support analytics
- HTTPS deployment and password-protected administration

## Multi-Agent Architecture

SupportIQ AI uses four specialized agents:

### 1. Query Agent
Analyzes customer requests and identifies their category, urgency, and sentiment.

### 2. Knowledge Agent
Retrieves relevant support policy information from the FAISS vector database.

### 3. Resolution Agent
Generates responses using retrieved knowledge and determines whether human escalation is required.

### 4. Log Agent
Records ticket details, AI responses, classification results, and resolution status.

## Workflow

Customer Query
    |
    v
Query Agent
    |
    v
Knowledge Agent (FAISS RAG)
    |
    v
Resolution Agent
    |
    +----> AI Resolution
    |
    +----> Human Escalation
                |
                v
         Admin Dashboard
                |
                v
       Assign / In Progress / Resolve

The Log Agent records support ticket information throughout the workflow.

## Knowledge Base

The application uses Markdown-based support documents covering:

- Shipping policies
- Refund policies
- Account and login support
- Product frequently asked questions

FAISS provides semantic retrieval of relevant policy content.

## Human Escalation

When a customer query requires human review, SupportIQ AI creates an escalated ticket.

Authorized administrators can:

1. Review escalated tickets.
2. Assign a support agent.
3. Mark the ticket as in progress.
4. Resolve the case.
5. Review the human action history.

## Technology Stack

| Layer | Technology |
|---|---|
| Programming | Python |
| Multi-Agent Framework | Microsoft AutoGen |
| LLM | OpenAI |
| RAG | LangChain and FAISS |
| Customer Portal | Streamlit |
| Admin Dashboard | Streamlit |
| Ticket Storage | CSV |
| Containerization | Docker Compose |
| Reverse Proxy | Traefik |
| HTTPS | Let's Encrypt |
| Hosting | Ubuntu VPS |

## Project Structure

```text
.
├── agents/
├── dashboard/
├── escalation/
├── knowledge_base/
├── vector_rag/
├── tests/
├── app.py
├── team.py
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

Runtime logs, authentication credentials, API keys, and generated FAISS indexes are excluded from version control.

## Local Setup

Requirements:
- Python 3.12
- OpenAI API key

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required API credentials in a local `.env` file.

Build the FAISS index using the ingestion script:

```bash
python -m vector_rag.ingest
```

Start the Customer Portal:

```bash
streamlit run app.py
```

Start the Admin Dashboard:

```bash
streamlit run dashboard/admin_dashboard.py
```

The local Admin Dashboard should be used only in a trusted environment unless separate authentication is configured.

## Docker Deployment

The production deployment uses two Streamlit containers:

- Customer Portal
- Admin Dashboard

Both containers share the support ticket logs and FAISS index through mounted directories.

Traefik provides HTTPS routing and Basic Authentication for the Admin Dashboard.

Authentication files and environment secrets are managed outside Git.

## Testing

Run the automated test suite:

```bash
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

The project has passed 10 automated tests covering ticket logging and escalation workflows.

## Demonstration Scenario

Customer query:

"Someone accessed my account without permission! I am worried about my personal information."

SupportIQ AI:

1. Classifies the query as Account.
2. Detects high urgency and negative sentiment.
3. Retrieves account security guidance.
4. Generates an appropriate response.
5. Escalates the security concern for human review.
6. Creates a support ticket.
7. Allows an administrator to assign and resolve the case.

## Security

- API credentials excluded from Git
- Authentication files excluded from Git
- HTTPS enabled through Traefik
- Admin Dashboard protected using Basic Authentication
- Application ports bound to localhost on the VPS
- Human review for sensitive or high-risk cases

## Future Enhancements

- Role-based access control
- Database-backed ticket management
- Customer email notifications
- SLA tracking and automated reminders
- Advanced support analytics
- Integration with enterprise CRM and ticketing platforms

## Buildathon Project

**SupportIQ AI — From Customer Query to Intelligent Resolution**

An end-to-end multi-agent customer support system combining AI automation, knowledge retrieval, human oversight, and cloud deployment.
