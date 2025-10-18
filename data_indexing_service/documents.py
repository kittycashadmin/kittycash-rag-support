# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

from pathlib import Path
import json
import pandas as pd
from PyPDF2 import PdfReader
from config import DOCSTORE_PATH
from feature_router import FeatureRouter  

_router = FeatureRouter()  

def _rows_from_file(file: Path):
    ext = file.suffix.lower()
    if ext == ".txt":
        for line in file.read_text(encoding="utf-8").splitlines():
            if "|" in line:
                yield [p.strip() for p in line.split("|", 1)]
    elif ext == ".pdf":
        text = ""
        for page in PdfReader(file).pages:
            text += (page.extract_text() or "") + "\n"
        for line in text.splitlines():
            if "|" in line:
                yield [p.strip() for p in line.split("|", 1)]
    elif ext == ".csv":
        df = pd.read_csv(file)
        if {"Question", "Answer"}.issubset(df.columns):
            for q, a in zip(df["Question"], df["Answer"]):
                yield str(q).strip(), str(a).strip()
    elif ext == ".xlsx":
        df = pd.read_excel(file)
        if {"Question", "Answer"}.issubset(df.columns):
            for q, a in zip(df["Question"], df["Answer"]):
                yield str(q).strip(), str(a).strip()
    elif ext == ".json":
        data = json.loads(file.read_text(encoding="utf-8"))
        for item in data:
            if "Question" in item and "Answer" in item:
                yield str(item["Question"]).strip(), str(item["Answer"]).strip()

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
        files = list(kb_path.glob("*.*"))
        if not files:
            return []

    existing_docs = []
    if Path(DOCSTORE_PATH).exists():
        try:
            existing_docs = json.loads(Path(DOCSTORE_PATH).read_text(encoding="utf-8"))
        except Exception:
            existing_docs = []
    start_id = len(existing_docs) + 1  # next available integer ID

    documents = []
    doc_id = start_id
    for file in files:
        try:
            for q, a in _rows_from_file(file) or []:
                if not q or not a:
                    continue
                text = f"{q} | {a}"
                feat = _router.detect_feature(text) or {}
                documents.append({
                    "id": doc_id,
                    "text": text,
                    "source": file.name,
                    "feature_id": feat.get("feature_id"),
                    "feature_name": feat.get("feature_name", "Uncategorized"),
                    "confidence": feat.get("confidence", 0.0),
                })
                doc_id += 1
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
    return documents


def save_docstore(documents):
    try:

        Path(DOCSTORE_PATH).write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
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
