# 🚀 SupportIQ AI — Intelligent Multi-Agent Customer Support

SupportIQ AI is an AI-powered customer support automation platform developed for the Buildathon using **Microsoft AutoGen, FAISS RAG, Streamlit, and Docker**.

It automates customer query classification, policy-based responses, conversation memory, ticket creation, and human escalation.

## 🌐 Live Application

- **Customer Portal:** https://supportiq.pbazskar.tech
- **Admin Dashboard:** https://supportiq-admin.pbazskar.tech (authentication required)
- **Skool:** https://www.skool.com/social-eagle-ai-6384/se-ai-b12-2week5buildathon-project-supportiq-ai?p=9033deee

## 🎯 Key Features

- **Multi-Agent Automation:** Four specialized AutoGen agents handle customer support.
- **Conversation Memory:** Remembers previous messages within the active session and understands follow-up questions.
- **FAISS RAG:** Retrieves relevant information from company policy documents.
- **Knowledge Validation:** Checks policy evidence and escalates when information is insufficient.
- **Intelligent Responses:** Generates policy-grounded answers without inventing unsupported details.
- **Ticket Management:** Automatically creates unique ticket IDs and logs support interactions.
- **Human Escalation:** Supports agent assignment, investigation, resolution, and audit history.
- **Admin Dashboard:** Displays ticket analytics, escalation queues, status tracking, and CSV export.
- **Cloud Deployment:** Dockerized applications hosted on Ubuntu VPS with Traefik and HTTPS.

## 🤖 Multi-Agent Architecture

| Agent | Responsibility |
|---|---|
| Query Agent | Classifies category, urgency, and sentiment |
| Knowledge Agent | Retrieves FAISS policy evidence and checks sufficiency |
| Resolution Agent | Generates customer-friendly, policy-grounded responses |
| Log Agent | Creates tickets and records support interactions |

### Workflow

```text
Customer Query / Follow-up
          |
          v
Conversation Memory
          |
          v
Context-Aware Query Rewriting
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
          v
Log Agent (Ticket Creation)
          |
          +----------------------+
          |                      |
          v                      v
     AI Response          Human Escalation
                                 |
                                 v
                          Admin Dashboard
                                 |
                                 v
                   Assign → Investigate → Resolve
                                 |
                                 v
                           Audit History
```

## 📚 Knowledge Base

FAISS retrieves relevant information from Markdown documents covering:

- Shipping and delivery
- Refunds and returns
- Account and login support
- Product FAQs

The Knowledge Agent checks whether retrieved evidence is sufficient. Unsupported questions are escalated for human review.

## 🔄 Improvements Implemented

### 1. Conversation Memory
- Added Streamlit session-based conversation history.
- Implemented context-aware follow-up handling.
- Added message counter and Clear Conversation option.

### 2. Knowledge Agent Improvements
- Validated FAISS retrieval and policy evidence.
- Enforced human escalation for insufficient evidence.
- Preserved high-urgency escalation.
- Prevented unsupported product and billing claims.

### 3. Human Escalation Validation
- Verified ticket assignment and investigation workflow.
- Confirmed resolution notes and audit history.
- Validated dashboard KPI updates.

### 4. Deployment Improvements
- Deployed updated Customer Portal using `supportiq-ai:memory-v3`.
- Maintained separate Customer Portal and Admin Dashboard containers.
- Verified shared persistent ticket logs and FAISS storage.
- Confirmed running containers and checked recent application logs.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming | Python 3.12 |
| AI Agents | Microsoft AutoGen |
| LLM & Embeddings | OpenAI |
| RAG | LangChain + FAISS |
| Frontend | Streamlit |
| Ticket Storage | CSV |
| Containerization | Docker Compose |
| Reverse Proxy | Traefik |
| HTTPS | Let's Encrypt |
| Hosting | Hostinger Ubuntu VPS |
| Version Control | GitHub |

## 📁 Project Structure

```text
SupportIQ-AI/
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
├── compose.memory.yaml
├── requirements.txt
└── README.md
```

Runtime logs, FAISS indexes, API keys, and authentication files are excluded from Git.

## 💻 Local Setup

```bash
git clone https://github.com/Prembazskar/Buildathon2_SupportIQ-AI-Customer-Support.git
cd Buildathon2_SupportIQ-AI-Customer-Support

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Configure `OPENAI_API_KEY` in `.env`, then build the FAISS index:

```bash
python -m vector_rag.ingest
```

Start the applications in separate terminals:

```bash
streamlit run app.py
streamlit run dashboard/admin_dashboard.py
```

The Admin Dashboard requires separate access protection when exposed beyond a trusted local environment.

## 🧪 Testing & Validation

Successfully tested:

- Customer complaint classification and AI responses
- FAISS policy retrieval and evidence validation
- Conversation memory and follow-up handling
- Automatic ticket creation and logging
- Human escalation for insufficient evidence
- Agent assignment, investigation, and resolution
- Escalation audit history and dashboard metrics
- Docker container status and recent application logs

**Example:** A duplicate-payment complaint was escalated and processed through:

`Pending Review → Assigned → In Progress → Resolved`

All three human actions were verified in the audit log. No real refund was performed.

## 🔐 Security & Limitations

- HTTPS enabled through Traefik.
- Admin Dashboard protected by Basic Authentication.
- API keys and runtime data excluded from Git.
- Application ports restricted to localhost on the VPS.
- Conversation memory is session-based.
- CSV ticket storage does not provide transactional concurrency control.
- No live payment, inventory, or order-tracking integrations.

## 🚀 Future Enhancements

- Role-based access control
- PostgreSQL ticket database
- Persistent customer conversation history
- Email notifications and SLA monitoring
- CRM and enterprise helpdesk integrations

## 🏆 Buildathon Outcome

**SupportIQ AI — From Customer Query to Intelligent Resolution**

Successfully built and deployed an end-to-end multi-agent customer support platform combining **Agentic AI, FAISS RAG, conversation memory, automated ticket management, human-in-the-loop escalation, and cloud deployment**.
