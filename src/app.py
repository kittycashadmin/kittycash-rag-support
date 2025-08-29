import argparse
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from .config import EMBED_MODEL, INDEX_DIR, DOCSTORE_PATH, KB_PATH, GEN_MODEL, TOP_K
from .vector_store import VectorStore
from .retriever import Retriever
from .generator import Generator
from .pipeline import RAGPipeline
from .utils import load_docstore, load_knowledge_base

def load_components():

    docs = load_docstore(DOCSTORE_PATH)
    if not docs:
        docs = load_knowledge_base(KB_PATH)

    vs = VectorStore(INDEX_DIR)
    vs.load()

    retriever = Retriever(EMBED_MODEL, vs, documents=docs)
    generator = Generator(GEN_MODEL)

    pipe = RAGPipeline(retriever, generator, top_k=TOP_K)
    return pipe


def cli():
    pipe = load_components()
    print("Kittycash Assistant")
    while True:
        q = input("\nAsk: ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        ans = pipe.ask(q)
        print("\nAssistant:", ans)

class AskRequest(BaseModel):
    question: str

def create_api():
    pipe = load_components()
    app = FastAPI(title="Kittycash Assistant API")

    @app.post("/ask")
    def ask(req: AskRequest):
        return {"answer": pipe.ask(req.question)}

    return app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cli", "api"], default="cli")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.mode == "cli":
        cli()
    else:
        app = create_api()
        uvicorn.run(app, host=args.host, port=args.port)
