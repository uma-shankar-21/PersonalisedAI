# BANKING-AI

An AI-powered personalized financial assistant built using:

* **Frontend:** React.js + TypeScript + MUI
* **Backend:** Python + Django + Django REST Framework
* **Database:** PostgreSQL + pgvector
* **LLM:** Llama 3 through Ollama
* **AI Orchestration:** LangChain
* **RAG / Retrieval:** LlamaIndex
* **Memory & Personalization:** PostgreSQL + pgvector
* **Cache / Background Processing:** Redis + Celery
* **Containerization:** Docker / Docker Compose

The application follows a **modular monolith architecture**. The frontend and backend are separate applications, while all backend functionality lives inside a single Django application.

---

# 1. Project Architecture

```text
BANKING-AI/
│
├── backend/
│   ├── venv/
│   ├── manage.py
│   ├── requirements.txt
│   │
│   ├── config/
│   │   └── settings/
│   │
│   ├── apps/
│   │   ├── users/
│   │   ├── banking/
│   │   ├── transactions/
│   │   ├── rewards/
│   │   ├── loans/
│   │   ├── assistant/
│   │   ├── memory/
│   │   ├── knowledge/
│   │   └── audit/
│   │
│   ├── common/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   └── styles/
│   │
│   └── package.json
│
├── docker/
│   ├── backend/
│   └── frontend/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

# 2. Prerequisites

Before starting, install the following:

### Required

* Git
* Python 3.11+
* Node.js LTS
* npm
* PostgreSQL
* Docker Desktop

### AI Development

* Ollama
* Llama 3 model

Check the installations:

```bash
git --version
python3 --version
node --version
npm --version
docker --version
```

On Windows, use:

```bash
python --version
```

instead of:

```bash
python3 --version
```

---

# 3. Clone the Repository

Clone the project:

```bash
git clone <REPOSITORY_URL>
```

Move into the project:

```bash
cd banking-ai
```

The project should contain:

```text
backend/
frontend/
README.md
.env.example
.gitignore
docker-compose.yml
```
Next Step is complete the 4th step completely and then go to Banking-AI folder(or your custom folder which has both frontend and backend in it, you can check this via running "ls" commad in terminal) and then run below command in terminal to start application.

```bash
docker compose up -d --build
```
---

# 4. Backend Setup

The backend is built using Python and Django.

Move into the backend:

```bash
cd backend
```

---

## 4.1 Create Python Virtual Environment

A virtual environment keeps this project's Python packages separate from other Python projects.

### macOS / Linux

Create the environment:

```bash
python3 -m venv myvenv
```

Activate it:

```bash
source myvenv/bin/activate
```

After activation, the terminal should look similar to:

```text
(myvenv) your-machine:backend$
```

### Windows

Create the environment:

```powershell
python -m venv myvenv
```

Activate it:

```powershell
myvenv\Scripts\activate
```

The terminal should show:

```text
(myvenv) your-machine:backend$
```

### Deactivate the environment

When finished working:

```bash
deactivate
```

To activate it again later:

### macOS / Linux

```bash
cd backend
source myvenv/bin/activate
```

### Windows

```powershell
cd backend
myvenv\Scripts\activate
```

> The `myvenv/` directory should not be committed to Git.

---

# 5. Frontend API Structure

The frontend will communicate with Django through:

```text
React
  ↓
api.service.ts
  ↓
Django REST API
```

`api.service.ts` will contain the common Axios configuration.

Other services will use it:

```text
auth.service.ts
       ↓
api.service.ts

banking.service.ts
       ↓
api.service.ts

assistant.service.ts
       ↓
api.service.ts
```

This prevents us from creating separate HTTP clients everywhere.

---

# 6. Environment Variables( `.env.example`)

The repository should contain:

```text
.env.example
```

but actual `.env` files should not be committed.

A root `.env.example` can document the variables required by the project:

```env
POSTGRES_DB=banking_ai
POSTGRES_USER=banking_ai
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

DJANGO_SECRET_KEY=change_me
DJANGO_DEBUG=True

VITE_API_BASE_URL=http://localhost:8000/api
```

For actual development, use the appropriate `.env` file for each application.

---

# 7. PostgreSQL + pgvector

Our database is:

```text
PostgreSQL
+
pgvector extension
```

They are not two separate databases.

Conceptually:

```text
PostgreSQL
│
├── users
├── accounts
├── transactions
├── loans
├── rewards
├── conversations
├── memories
│
└── vector data
       ├── user memory embeddings
       └── knowledge embeddings
```

The PostgreSQL Docker image will eventually use:

```yaml
image: pgvector/pgvector:pg16
```

This provides PostgreSQL with the pgvector extension.

We will enable the extension during the database setup.

---

# 8. Redis

Redis is not our primary database.

PostgreSQL stores permanent application data.

Redis will later be used for:

```text
Caching
Rate limiting
Temporary state
Celery task queue
Background processing
```

For example:

```text
Django
   ↓
Redis
   ↓
Celery Worker
   ↓
Memory processing
```

Redis is therefore part of the architecture, but some of its functionality will be implemented later.

---

# 9. Ollama

Ollama will run Llama 3 locally.

Install Ollama separately and verify:

```bash
ollama --version
```

Download the model:

```bash
ollama pull llama3
```

Run it:

```bash
ollama run llama3
```

The Ollama API normally runs at:

```text
http://localhost:11434
```

Our Django backend will communicate with Ollama.

```text
Django
   ↓
Ollama
   ↓
Llama 3
```

We will connect this after the basic Django application is working.

---

# 10. Docker

Docker will eventually run:

```text
Frontend
Backend
PostgreSQL + pgvector
Redis
```

The project will use:

```text
docker-compose.yml
```

The initial Docker architecture will be:

```text
Docker Compose
│
├── frontend
├── backend
├── postgres
└── redis
```

Ollama may initially run directly on the development machine because local GPU/hardware access makes that setup simpler.

Docker configuration will be finalized after the local applications are working.

---

# 11. Verify Django

From:

```text
backend/
```

activate the virtual environment.

Then:

```bash
python manage.py check
```

If everything is correct:

```text
System check identified no issues.
```

Start Django:

```bash
python manage.py runserver
```

The backend should be available at:

```text
http://localhost:8000
```

---

# 12. Verify React

From:

```text
frontend/
```

run:

```bash
npm run dev
```

The frontend should be available at:

```text
http://localhost:5173
```

---

# 13. Development Workflow

Every time you start working on the project:

### Terminal 1 — Backend

```bash
cd banking-ai/backend
source myvenv/bin/activate
python manage.py runserver
```

Windows:

```powershell
cd banking-ai/backend
myvenv\Scripts\activate
python manage.py runserver
```

### Terminal 2 — Frontend

```bash
cd banking-ai/frontend
npm run dev
```

### Terminal 3 — Ollama

```bash
ollama run llama3
```

Later, Docker Compose will simplify this workflow.

---

# 14. AI Safety Requirements

The Financial Assistant must follow these rules.

### It MUST:

* Answer banking/financial-assistant related questions.
* Use customer-specific data only after authorization.
* Use controlled tools instead of direct database access.
* Base financial claims on retrieved data.
* Provide evidence for important financial conclusions.
* Respect customer-specific memory and preferences.
* Reject unrelated topics.
* Protect customer data.
* Handle prompt injection attempts.
* Validate AI-generated responses.

### It MUST NOT:

* Directly access PostgreSQL.
* Execute arbitrary SQL generated by the LLM.
* Access another customer's information.
* Invent balances, transactions, loans or rewards.
* Reveal sensitive information.
* Execute financial transactions in the initial version.
* Treat transaction descriptions or external documents as trusted instructions.
* Answer arbitrary unrelated questions.

---

# 15. Target AI Architecture

The final AI request flow will look approximately like:

```text
Customer
   │
   ▼
React
   │
   ▼
Django API
   │
   ▼
Domain Guard
   │
   ├── Unrelated → Fallback Response
   │
   ▼
Memory Retrieval
   │
   ▼
LangChain Orchestration
   │
   ▼
MCP / Controlled Tools
   │
   ├── Transactions
   ├── Accounts
   ├── Loans
   └── Rewards
   │
   ▼
Django Services
   │
   ▼
PostgreSQL
   │
   ▼
Verified Financial Data
   │
   ▼
Context Builder
   │
   ▼
Llama 3 / Ollama
   │
   ▼
Response Validation
   │
   ▼
Evidence
   │
   ▼
React
```

The LLM will **not** receive unrestricted database access.

---

# 16. Important Development Rule

Do not install random packages whenever a new problem appears.

Before adding a dependency, determine:

1. What problem does it solve?
2. Do we actually need it?
3. Can Django/Python/React already solve it?
4. Does it fit the architecture?
5. Does it introduce unnecessary complexity?

The goal is to build a system that is understandable, secure and maintainable—not a project containing every popular AI library.

---

# 17. Current Architecture Summary

```text
Frontend
    React + TypeScript + MUI
              │
              ▼
Backend
    Django + DRF
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
 PostgreSQL  Redis    Ollama
 + pgvector           Llama 3
      │
      ▼
User data
Memory
Embeddings
Banking data
```

The application is a:

> **Modular Django Monolith with an AI-powered personalized financial assistant.**

The AI layer will use:

> **LangChain for orchestration + MCP for controlled tools + LlamaIndex for retrieval/RAG + Llama 3 through Ollama + PostgreSQL/pgvector for memory and embeddings.**

This README describes the **initial development setup**. Detailed implementation of the banking models, authentication, MCP tools, memory system, RAG pipeline, AI guardrails and evidence system will be added as development progresses.
