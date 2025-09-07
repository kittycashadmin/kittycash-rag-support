# Kitty Cash Microservices

![alt text](images/1_n6sn9S_gXhvIXC8vSCz8zw.webp)

## Overview
- **Data Indexing Service:** Loads chitfund workflows, creates BGE-M3 embeddings, builds FAISS vector indexes.
- **Retrieval Service:** Embeds user queries, searches FAISS index for relevant documents.
- **Generation Service:** Generates responses using local large language model (Mistral-7B-Instruct/Llama3) with context.
- **API Service:** Coordinates calls between retrieval and generation services; exposes unified query API.

---

## Architecture
![KC](images/image.png)

---

## Data Indexing Service

**Purpose:** Load knowledge base documents and index them in FAISS using BGE-M3 embeddings.

**Key Features:**
- Converts text documents to vector embeddings.
- Builds and saves FAISS index and document store.
- REST endpoints for health check, index rebuild, and index status.

---

## Retrieval Service

**Purpose:** Accept user queries, embed with BGE-M3, and search FAISS index for top-k documents.

**Key Features:**
- Loads FAISS index and document store at startup.
- Returns documents and similarity scores.
- REST endpoints for health check and search.

---

## Generation Service

**Purpose:** Format prompt with system rules and context, invoke local LLM, and return generated response.

**Key Features:**
- Enforces chitfund-specific guidelines and privacy rules.
- Uses Ollama to run local LLM model.
- REST endpoints for health check and answer generation.

---

## API  Service

**Purpose:** Provide unified API endpoint, coordinate retrieval and generation calls asynchronously.

**Key Features:**
- Routes user queries to retrieval and generation services.
- Handles errors and logs operations.
- CORS enabled for cross-origin access.

