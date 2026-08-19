1. cd backend -> For mac : python3 -m venv myvenv, source myvenv/bin/activate, (myvenv) your-machine:backend$
                For windows: python -m venv myvenv, myvenv\Scripts\activate, (myvenv) your-machine:backend$
                to stop command : deactivate
2. cd frontend ->  node --version , npm install, npm run dev(need to rewrite)
3. cd backend -> pip install django djangorestframework "psycopg[binary]" python-dotenv
              -> django-admin startproject config . this gives
                    backend/
                    ├── manage.py
                    └── config/
                        ├── __init__.py
                        ├── settings.py
                        ├── urls.py
                        ├── asgi.py
                        └── wsgi.py
    We're going to convert settings.py into:

                        config/settings/
                        ├── __init__.py
                        ├── base.py
                        ├── development.py
                        └── production.py
4. mkdir apps, touch apps/__init__.py and then use to create apps(simply services)
                    python manage.py startapp users apps/users
                    python manage.py startapp banking apps/banking
                    python manage.py startapp transactions apps/transactions
                    python manage.py startapp rewards apps/rewards
                    python manage.py startapp loans apps/loans
                    python manage.py startapp assistant apps/assistant
                    python manage.py startapp memory apps/memory
                    python manage.py startapp knowledge apps/knowledge
                    python manage.py startapp audit apps/audit
5. creating nessasy file command:
    mkdir -p assistant/services assistant/guards assistant/tools assistant/mcp assistant/llm assistant/tests && touch assistant/__init__.py assistant/admin.py assistant/apps.py assistant/models.py assistant/urls.py assistant/views.py assistant/serializers.py assistant/services/__init__.py assistant/services/chat.service.py assistant/services/context.service.py assistant/services/response.service.py assistant/guards/__init__.py assistant/guards/domain.guard.py assistant/guards/prompt.guard.py assistant/guards/output.guard.py assistant/tools/__init__.py assistant/tools/account.tools.py assistant/tools/transaction.tools.py assistant/tools/loan.tools.py assistant/tools/reward.tools.py assistant/mcp/__init__.py assistant/mcp/server.py assistant/mcp/tools.py assistant/llm/__init__.py assistant/llm/ollama.client.py assistant/llm/prompts.py

    mkdir -p memory/services memory/repositories memory/tests && touch memory/__init__.py memory/admin.py memory/apps.py memory/models.py memory/services/__init__.py memory/services/memory_service.py memory/services/memory_extractor.py memory/services/memory_retriever.py memory/services/memory_updater.py memory/repositories/__init__.py memory/repositories/memory_repository.py

    mkdir -p knowledge/services knowledge/loaders knowledge/embeddings knowledge/tests && touch knowledge/__init__.py knowledge/admin.py knowledge/apps.py knowledge/models.py knowledge/services/__init__.py knowledge/services/ingestion_service.py knowledge/services/embedding_service.py knowledge/services/retrieval_service.py knowledge/loaders/__init__.py knowledge/embeddings/__init__.py

6. cd frontend, npm create vite@latest . -- --template react-ts, and select esclint
        and run npm install axios react-router-dom, npm install @mui/material @emotion/react @emotion/styled

    Required Files: cd ..                                                   
                    mkdir -p frontend/src/api frontend/src/components/common frontend/src/components/layout frontend/src/components/assistant frontend/src/pages/Login frontend/src/pages/Dashboard frontend/src/pages/Assistant frontend/src/hooks frontend/src/types frontend/src/utils frontend/src/styles && touch frontend/src/api/api.service.ts frontend/src/api/auth.service.ts frontend/src/api/banking.service.ts frontend/src/api/assistant.service.ts frontend/src/types/auth.types.ts frontend/src/types/banking.types.ts frontend/src/types/assistant.types.ts frontend/.env frontend/.env.example
7. 