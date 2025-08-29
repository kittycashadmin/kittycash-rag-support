from pathlib import Path
import json
import re

def load_knowledge_base(kb_path: str):
    text = Path(kb_path).read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.split("\n---\n") if b.strip()]
    docs = []
    for b in blocks:
        m = re.search(r"^### DOC_ID:\s*(\d+)", b, flags=re.MULTILINE)
        doc_id = int(m.group(1)) if m else len(docs) + 1
        b_clean = re.sub(r"^### DOC_ID:.*\n?", "", b, count=1, flags=re.MULTILINE).strip()
        docs.append({"id": doc_id, "text": b_clean, "meta": {}})
    return docs

def save_docstore(docstore_path: str, documents):
    data = [{"id": d["id"], "text": d["text"], "meta": d.get("meta", {})} for d in documents]
    Path(docstore_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_docstore(docstore_path: str):
    p = Path(docstore_path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))
