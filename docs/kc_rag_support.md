# Kitty Cash Microservices

## Setup

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally
- Pull a local LLM (LLaMA 3.2 )
  ```bash
  ollama pull llama3.2:latest 
  ```


### Set up data:
- Place your `knowledge_base.txt` in `data/`.
- The FAISS index and docstore.json will be generated automatically.

Each service has its own dependencies. Generally, you should:

### Install Python deps for each service

```bash
pip install -r requirements.txt
```

### Always ensure both retrieval and generation services are running before starting or using the API server.


## Architecture

![alt text](images/1_n6sn9S_gXhvIXC8vSCz8zw.webp)

## Overview
- **Data Indexing Service:** Loads kittycash workflows, creates BGE-M3 embeddings, builds FAISS vector indexes.
- **Retrieval Service:** Embeds user queries, searches FAISS index for relevant documents.
- **Generation Service:** Generates responses using local large language model (Llama3) with context.
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

**Purpose:** Provide unified endpoint.

**Key Features:**
- Sends user query to MCP client
- Handles tool execution via MCP
- Logs all operations and errors

## MCP Client
**Purpose:** Central orchestrator for tool execution using Router LLM.
- Uses LLM to decide which tools to call first
- Fallback to retriever → generator if LLM fails
- Ensures context is never returned directly
- Supports retriever, generator, indexer
---
## MCP Server
**Purpose:** server acts as the central hub for managing tool execution requests in the Kitty Cash system. It provides a streamable, async interface for the MCP client to call tools such as retriever, generator, and indexer.
- list of available tools and their capabilities
- Receives tool call requests and routes them to the appropriate service.
---
# MCP WORKFLOW

![KC](images/mcp+rag.png)

### Kitty Cash Query Workflow

1. **User sends a question** via the API endpoint.

2. **MCP Client** receives the question and asks the **Router LLM** which tools to use.

   - If the question needs facts → Plan: `retriever` → `generator`.
   - If the question is creative → Plan: `generator` only.

3. **MCP Server** executes each tool step:

   - **Retriever:** Searches the FAISS index and returns relevant documents.
   - **Generator:** Takes the query + optional context to produce the final answer using **local LLM (Llama3)**.

4. **Final answer** is returned to the API Service → sent to the user.

If testing in local  first install the requirements and run the each micreservice as mention below: 

### Step 1: Start Data Indexing Service
Generates FAISS index and docstore from the knowledge base:

```bash
uvicorn data_indexing_service.app:app --port 8001 --reload
```
### Step 2: Start Retrieval Service
Searches the FAISS index for relevant documents:
```bash
uvicorn retrieval_service.app:app --port 8002 --reload
```
### Step 3: Start Generation Service
Generates answers using LLaMA 3:
```bash
uvicorn generation_service.app:app --port 8003 --reload
```

### Step 4: Start MCP Server
Executes tool steps  and orchestrates MCP Client:
```bash
python mcp_server.server.py
```

### Step 5: Start Data Indexing Service
Exposes  endpoint to receive user queries and upload files
```bash
uvicorn api_service.app:app --port 8000 --reload
```
### command to test the API service:

```bash
curl -X POST http://127.0.0.1:8000/support/chat \
-H "Content-Type: application/json" \
-d '{
    "user_id": "123",
    "message": "What is Kitty Cash?"
}'
```

### To build docker
```bash
docker-compose up --build
```
### Pre-pull Models
```bash
docker exec -it ollama ollama pull llama2
```


# Data Indexing service

### Indexer.py

## FAISS (Facebook AI Similarity Search)

 - A library for efficient similarity search in large vector datasets.
 - Supports two types of indexes:
     - Flat Index → Stores all vectors as it is and compare wiyh eachother.
     - IVF Index (Inverted File) → Clusters vectors into groups (centroids) for faster search, better for large datasets.
 - Dynamic nlist (clusters) : Instead of fixing number of clusters, nlist is chosen based on dataset size.
 - IVF Index requires "training" to find cluster centroids before adding data.

## Role: 
 - Handles FAISS Index Management (building, adding, saving, loading).
 - Build a new FAISS index from embeddings.
 - Add new embeddings into an existing index.
 - Save index files (.index) and metadata (.meta.json).
 - Load existing index (by version or latest).

**build**
- Create a new FAISS index from given embeddings.
```bash
FUNCTION build(embeddings):
    CHECK if embeddings are in 2D shape [rows, columns]
        IF NOT, throw error

    SET dimension = number of columns in embeddings
    SET num_vectors = number of rows in embeddings

    IF num_vectors is small (less than 100):
        CREATE a simple Flat index using Inner Product
        ADD all embeddings to this index
        PRINT "Flat index built"
    ELSE:
        CALCULATE number of clusters = (num_vectors / 4), but max 100
        CREATE a quantizer (Flat index)
        CREATE an IVF index using quantizer, dimension, and clusters
        TRAIN IVF index with embeddings
        ADD embeddings to IVF index
        PRINT "IVF index built"

    RETURN the index

```


**save**
- Save the FAISS index + metadata to disk.
```bash
FUNCTION save(version, docs_added):
    IF no index exists:
        RAISE error "No index to save"

    SET index_path = "index_dir/version.index"
    WRITE index to index_path

    CREATE metadata = {
        "version": version,
        "dim": index_dimension,
        "doc_count": docs_added,
        "created_at": current_timestamp
    }

    SET meta_path = "index_dir/version.meta.json"
    WRITE metadata as JSON file to meta_path

    PRINT "Index and metadata saved"

```
### documents.py
## Role:
 - Load KB files (.txt) line by line into structured document objects.
 - Maintain docstore.json (the central record of all documents).
 - Reload saved documents when restarting service.

**load_kb_files**

```bash
FUNCTION load_kb_files(kb_dir, kb_file optional):
    SET kb_path = directory where KB files are stored

    IF kb_file is provided:
        SET file_path = kb_file
        IF file_path does not exist:
            TRY kb_dir/kb_file
            IF still does not exist:
                RETURN empty list
        files = [file_path]
    ELSE:
        files = all *.txt files in kb_dir
        IF no files:
            RETURN empty list

    documents = []
    doc_id = 1

    FOR each file in files:
        TRY:
            READ file line by line
            FOR each line:
                CLEAN line (remove spaces)
                IF not empty:
                    ADD to documents:
                        { "id": doc_id, "text": line, "source": filename }
                    INCREMENT doc_id
        EXCEPT error:
            PRINT error and skip file

    RETURN documents
```

### app.py

## Role:
-  Startup logic → loads existing index or builds the first one if missing.
- /health → health check for monitoring.
- /index/add → add new KB files into the index.
- /index/status → check latest index version, dimensions, and stats.

**startup_event()**
- Runs automatically when the server starts. Loads the latest index if available, otherwise creates the first one.
```bash
FUNCTION startup_event():
    TRY:
        LOAD latest index from disk
        LOAD document store
        SET current_version to latest index version
        PRINT "Index loaded"
    EXCEPT FileNotFoundError:
        LOAD all knowledge base (KB) files
        IF no documents found:
            RAISE error "Knowledge base is empty"
        CONVERT all document texts into embeddings
        BUILD a new FAISS index with embeddings
        ASSIGN version = get_next_version()
        SAVE index and metadata with this version
        SAVE document store
        PRINT "Created initial index"
```
**/index/add**
- Add new documents to the existing index.
```bash
ROUTE GET /index/add (kb_file optional):
    IF kb_file is provided:
        CHECK if kb_file exists in given or KB directory
        LOAD new documents from this file
    ELSE:
        LOAD all documents from KB directory

    FILTER out documents that already exist in memory

    IF no fresh documents:
        RETURN "No new KB documents to add" + total_docs_count

    CONVERT fresh document texts into embeddings
    ADD embeddings into FAISS index
    EXTEND document store with fresh docs
    ASSIGN version = get_next_version()
    SAVE updated index with new version
    SAVE updated document store

    RETURN success message with added_docs_count, total_docs_count, and version
```

# Retreval Server

## retriever.py
## Role:
 - Takes a user query (text input).
 - Converts it into an embedding (vector representation).
 - Uses FAISS to find the most relevant documents from the index.
 - Returns those documents with relevance scores.

**load_index**
```bash
FUNCTION load_index():
    FIND all metadata JSON files in index_dir
    IF none exist:
        RAISE error "No index found"

    SELECT latest version (last metadata file)
    READ metadata to get version + dimension
    CONSTRUCT path to FAISS index file
    IF file does not exist:
        RAISE error "Index file missing"

    LOAD FAISS index from file
    SET self.dim = index dimension
    PRINT confirmation
```
**search(query)**
```bash
FUNCTION search(query):
    CONVERT query text into embedding (vector) using embedder
    NORMALIZE embedding for better similarity scores
    SEARCH FAISS index with embedding → return top_k results
    results = []

    FOR each score, index in search results:
        IF index is valid (not -1 and within documents range):
            GET document from documents list
            APPEND { "score": score, "document": doc } to results

    RETURN results
```

## app.py
- Exposes your Retriever class via a FastAPI service.
- Provides endpoints so external apps (frontend, chatbot, etc.) can:
- Check if the service is running (/health)
- Run semantic search queries (/search?query=...)
- This is the search API your system provides.

```bash
Start FastAPI app with service name "Retrieval Service"

Initialize retriever with:
    - embedding model
    - FAISS index path
    - document store path
    - top_k parameter

Define endpoint /health:
    return "Retrieval Service running"

Define endpoint /search with parameter query:
    if query is missing:
        return error 400 "Query is required"
    results = retriever.search(query)
    return { "query": query, "results": results }
```

# Generation_service

- Generator class → Runs LLM using subprocess (ollama run).
- SYSTEM_RULES → Predefined rules to control LLM output (no assumptions, professional tone, follow retrieved context only).
- format_prompt → Combines SYSTEM_RULES, context, and user query into a single prompt for the LLM.
- TOP_K → Only the top-K retrieved documents are sent to LLM for efficiency and relevance.


**generator.py**

```bash

FUNCTION format_prompt(context_blocks, user_query):
    context_text = ""
    FOR each context_block in context_blocks:
        context_text += "[DOC {id}]\n{text}\n\n"

    prompt = """
    SYSTEM_RULES

    [CONTEXT]
    {context_text}

    [USER QUESTION]
    {user_query}

    [ASSISTANT RESPONSE]
    """
    RETURN prompt

FUNCTION generate(prompt):
    RUN subprocess:
        ["ollama", "run", self.model]
        INPUT: prompt (encoded as UTF-8)
        CAPTURE stdout & stderr

    IF return code != 0:
        RAISE RuntimeError("LLM generation failed: {stderr}")

    RETURN stdout as generated answer (decoded & stripped)
```

**app.py**

```bash
POST /generate/ with JSON { "user_query": str, "context": [Document] }:

    IF user_query or context is missing:
        RETURN 400 error "user_query and context are required"

    # Step 1: Prepare prompt for LLM
    TAKE top TOP_K context documents
    FORMAT prompt using SYSTEM_RULES + context + user_query

    # Step 2: Generate answer using LLM
    TRY:
        answer = generator.generate(prompt)
    EXCEPT any error:
        RETURN 500 error with error message

    RETURN { "answer": answer }
```
# API_Service

## Role

- Receives user message from frontend.
- Sends the message to retrieval service to get relevant documents.
- Sends retrieved context + user query to generation service to get final answer.
- Returns the answer back to the frontend.

```bash

POST /support/chat with JSON { "user_id": str, "message": str }:

    EXTRACT user_message and user_id from request
    IF user_message OR user_id is missing:
        RETURN 400 error "Missing message or user_id"

    LOG "Received message from user {user_id}"

    TRY:
        # Step 1: Call retrieval service
        SEND GET request to RETRIEVAL_SERVICE_URL /search with query=user_message
        PARSE response and take top_k documents as context_docs
        LOG "Retrieved {len(context_docs)} documents from retrieval service"

        # Step 2: Prepare payload for generation service
        context = [doc["document"] for doc in context_docs]
        gen_payload = { "user_query": user_message, "context": context }
        LOG "Sending context to generation service"

        # Step 3: Call generation service
        SEND POST request to GENERATION_SERVICE_URL /generate with gen_payload
        PARSE response to get "answer"
        LOG "Generated answer for user {user_id}"

        RETURN {
            "status": "success",
            "responses": [
                { "type": "text", "content": answer }
            ]
        }

    EXCEPT httpx.RequestError:
        LOG "Request error"
        RETURN 503 error "Service unavailable"

    EXCEPT httpx.HTTPStatusError:
        LOG "HTTP error"
        RETURN the same HTTP error code + message

```