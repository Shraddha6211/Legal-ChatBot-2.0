#!/bin/bash

# create folders
mkdir -p backend/api \
         backend/core \
         backend/db \
         backend/memory \
         backend/tools \
         backend/prompts \
         frontend \
         tests

# create __init__.py files
touch backend/__init__.py
touch backend/api/__init__.py
touch backend/core/__init__.py
touch backend/db/__init__.py
touch backend/memory/__init__.py
touch backend/tools/__init__.py
touch backend/prompts/__init__.py

# create backend files
touch backend/main.py
touch backend/api/routes.py
touch backend/core/ingest.py
touch backend/core/retriever.py
touch backend/core/chains.py

# create database files
touch backend/db/pinecone_client.py
touch backend/db/redis_client.py

# create memory files
touch backend/memory/session.py
touch backend/memory/cache.py

# create tool files
touch backend/tools/search.py
touch backend/tools/memory.py
touch backend/tools/article.py

# create prompt files
touch backend/prompts/templates.py

# create frontend files
touch frontend/app.py

# create test files
touch tests/test_retrieval.py
touch tests/test_memory.py
touch tests/test_tools.py

# create root files
touch config.py
touch .env
touch .env.example
touch requirements.txt
touch README.md

echo "Project structure created successfully!"