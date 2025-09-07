from pathlib import Path
import json
import re
from config import KB_PATH, DOCSTORE_PATH

def load_knowledge_base():
    text = Path(KB_PATH).read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.split("\n---\n") if b.strip()]
    docs = []
    for i, b in enumerate(blocks):
        docs.append({"id": i+1, "text": b})
    return docs

def save_docstore(documents):
    data = [{"id": d["id"], "text": d["text"]} for d in documents]
    Path(DOCSTORE_PATH).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_docstore():
    p = Path(DOCSTORE_PATH)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))
