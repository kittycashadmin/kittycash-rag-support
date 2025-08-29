# Kittycash Virtual Assistant


## Setup

### 1) Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally
- Pull a local LLM (LLaMA 3.2 or Mistral)
  ```bash
  ollama pull llama3.2:latest or 
  ollama pull mistral  
  ```

### 2) Install Python deps
```bash
pip install -r requirements.txt
```

### 3) Build the index (from `data/knowledge_base.txt`)
```bash
python -m scripts.build_index
```
This creates:
- `data/faiss_index/index.faiss`
- `data/docstore.json`

### 4) Run the assistant (CLI)
```bash
python -m src.app --mode cli
```

### 5) Run as an API (FastAPI)
```bash
python -m src.app --mode api --host 0.0.0.0 --port 8000
```

### Run the Docker Container

## Prerequisites
- Ollama installed and running locally on the host machine


## Build Docker Image
docker build -t kittycash-assistant .

## Run Container
docker container : docker run --rm -it --network host \
  -v /usr/local/bin/ollama:/usr/local/bin/ollama:ro \
  -v $(pwd)/data:/app/data \
  kittycash-assistant python -m src.app --mode api --host 0.0.0.0 --port 8000     (will be removed if exit the container)

docker run -dit --name kittycash-container --network host -v $(pwd)/data:/app/data kittycash-assistant python -m src.app --mode api --host 0.0.0.0 --port 8000
