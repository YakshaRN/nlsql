backend/
├── app/
│   ├── main.py                # FastAPI entrypoint
│   ├── api.py                 # HTTP routes
│   ├── models.py              # Pydantic schemas
│   ├── llm/
│   │   ├── bedrock_client.py
│   │   ├── prompts.py
│   │   └── intent_resolver.py
│   ├── queries/
│   │   ├── registry.py
│   │   └── sql_templates.py
│   ├── db/
│   │   ├── connection.py
│   │   └── executor.py
│   ├── context/
│   │   └── memory.py
│   └── utils/
│       └── sql_guard.py
├── requirements.txt
└── README.md
