from pathlib import Path
import json
from config import DOCSTORE_PATH

def load_kb_files(kb_dir: str, kb_file: str = None):
    kb_path = Path(kb_dir)
    if kb_file:
        file_path = Path(kb_file)
        if not file_path.exists():
            file_path = kb_path / kb_file
            if not file_path.exists():
                return []
        files = [file_path]
    else:
        files = list(kb_path.glob("*.txt"))
        if not files:
            return []
    documents = []
    doc_id = 1  
    for file in files:
        try:
            for line in file.read_text(encoding="utf-8").splitlines():
                text = line.strip()
                if text:
                    documents.append({"id": doc_id, "text": text, "source": str(file.name)})
                    doc_id += 1
        except Exception as e:
            print(f"Error reading {file}: {str(e)}")
            continue
    return documents

def save_docstore(documents):
    try:
        data = [{"id": d["id"], "text": d["text"], "source": d.get("source", "")} for d in documents]
        Path(DOCSTORE_PATH).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error saving docstore: {str(e)}")

def load_docstore():
    p = Path(DOCSTORE_PATH)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error loading docstore: {str(e)}")
        return []