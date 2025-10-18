import json
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Feature, Question
from error_responses import raise_api_error
from config import RETRIEVER_URL, MAX_BULK_IDS,API_SERVER_URL 
from urllib.parse import quote_plus
import httpx
import logging
from cache import redis_client
import hashlib



logger = logging.getLogger(__name__)

def list_features(db: Session) -> List[Dict[str, Any]]:
    rows = db.query(Feature).order_by(Feature.id).all()
    return [{"id": f.id, "name": f.name, "is_modified": f.is_modified} for f in rows]

def get_feature(db: Session, feature_id: int) -> Feature:
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)
    return f

def create_feature(db: Session, name: str, description_str: Optional[str]) -> Feature:
    existing = db.query(Feature).filter(func.lower(Feature.name) == name.lower()).first()
    if existing:
        raise_api_error("DUPLICATE_FEATURE_NAME", "Feature name already exists", 409)

    parsed_desc = None
    if description_str is not None:
        try:
            parsed_desc = json.loads(description_str)
        except Exception:
            raise_api_error("VALIDATION_ERROR", "Invalid description JSON", 400, details={"field_errors": [{"field": "description", "message": "Must be valid Quill Delta JSON string"}]})

    f = Feature(name=name.strip(), description=parsed_desc, is_modified=True)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f

def update_feature(db: Session, feature_id: int, description_str: Optional[str]) -> Feature:
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    parsed_desc = None
    if description_str is not None:
        try:
            parsed_desc = json.loads(description_str)
        except Exception:
            raise_api_error("VALIDATION_ERROR", "Invalid description JSON", 400, details={"field_errors": [{"field": "description", "message": "Must be valid Quill Delta JSON string"}]})

    f.description = parsed_desc
    f.is_modified = True
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def list_questions(db: Session, feature_id: int, status: Optional[int] = None) -> Dict[str, Any]:
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    q = db.query(Question).filter(Question.feature_id == feature_id)
    if status is not None:
        if status not in (1, 2):
            raise_api_error("VALIDATION_ERROR", "Invalid status filter", 400)
        q = q.filter(Question.status == status)
    rows = q.order_by(Question.id.desc()).all()
    items = [ {
        "id": r.id,
        "feature_id": r.feature_id,
        "question": r.question,
        "answer": r.answer,
        "status": r.status,
        "created_at": r.created_at,
        "updated_at": r.updated_at
    } for r in rows ]
    return {"items": items, "pagination": {"current_page": 1, "total_pages": 1, "total_items": len(items), "items_per_page": len(items)}}

def create_question(db: Session, feature_id: int, question_text: str, answer_text: str) -> Question:
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    q = Question(feature_id=feature_id, question=question_text.strip(), answer=answer_text.strip(), status=1)
    db.add(q)
    f.question_count = f.question_count + 1
    db.add(f)
    db.commit()
    db.refresh(q)
    return q

def update_question(db: Session, feature_id: int, question_id: int, question_text: Optional[str], answer_text: Optional[str]) -> Question:
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    q = db.query(Question).filter(
        Question.feature_id == feature_id,
        Question.id == question_id
    ).first()
    if not q:
        raise_api_error("QUESTION_NOT_FOUND", "Question not found", 404)

    
    changed = False
    if question_text is not None:
        q.question = question_text.strip()
        changed = True
    if answer_text is not None:
        q.answer = answer_text.strip()
        changed = True

    if not changed:
        raise_api_error("VALIDATION_ERROR", "No update fields provided", 400)

    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def submit_questions(db: Session, feature_id: int, question_ids: List[int]) -> Dict[str, List[int]]:
    if not question_ids:
        raise_api_error("EMPTY_IDS", "question_ids missing or empty", 400)

    if len(question_ids) > MAX_BULK_IDS:
        raise_api_error("VALIDATION_ERROR", f"Too many ids in batch (max {MAX_BULK_IDS})", 400)

    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    rows = db.query(Question).filter(Question.feature_id == feature_id, Question.id.in_(question_ids)).all()
    found_ids = {r.id: r for r in rows}
    submitted_ids = []
    failed_ids = []

    for qid in question_ids:
        q = found_ids.get(qid)
        if not q:
            failed_ids.append(qid)
            continue
        if q.status == 2:
            failed_ids.append(qid)
            continue
        q.status = 2
        db.add(q)
        submitted_ids.append(qid)

    db.commit()
    return {"submitted_ids": submitted_ids, "failed_ids": failed_ids}

def delete_questions(db: Session, feature_id: int, question_ids: List[int]) -> Dict[str, List[int]]:
    if not question_ids:
        raise_api_error("EMPTY_IDS", "question_ids missing or empty", 400)

    if len(question_ids) > MAX_BULK_IDS:
        raise_api_error("VALIDATION_ERROR", f"Too many ids in batch (max {MAX_BULK_IDS})", 400)

    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    rows = db.query(Question).filter(Question.feature_id == feature_id, Question.id.in_(question_ids)).all()
    found_ids = {r.id: r for r in rows}
    deleted_ids, restored_ids, failed_ids = [], [], []

    for qid in question_ids:
        q = found_ids.get(qid)
        if not q:
            failed_ids.append(qid)
            continue

        # Draft only deletion logic
        if q.status == 2:
            failed_ids.append(qid)
            continue

        # If this draft originated from a final (you can mark that in future via metadata)
        if hasattr(q, "original_final_id") and q.original_final_id:
            restored_ids.append(q.original_final_id)

        db.delete(q)
        deleted_ids.append(qid)
        f.question_count = max(0, f.question_count - 1)
        db.add(f)

    db.commit()
    return {"deleted_ids": deleted_ids, "restored_ids": restored_ids, "failed_ids": failed_ids}



def get_questions_by_ids(db, feature_id: int, ids: List[int]):
    if not ids:
        return []
    return db.query(Question).filter(Question.feature_id == feature_id, Question.id.in_(ids)).all()




    #def sync_features_from_retriever(db):
    # try:
    #     with httpx.Client(timeout=600.0) as client:
    #         resp = client.get(f"{RETRIEVER_URL}/features")
    #     if resp.status_code != 200:
    #         raise_api_error("INTERNAL_ERROR", "Failed to fetch features from retriever", 500)
    #     retriever_features = resp.json().get("features", [])
    # except Exception as e:
    #     raise_api_error("INTERNAL_ERROR", f"Retriever sync error: {e}", 500)

    # added, updated, skipped = 0, 0, 0

    # for rf in retriever_features:
    #     name = rf["name"].strip()
    #     desc = rf.get("description")
    #     existing = db.query(Feature).filter(func.lower(Feature.name) == name.lower()).first()

    #     if not existing:
    #         f = Feature(
    #             name=name,
    #             description=None if not desc else json.loads(json.dumps(desc)),
    #             is_modified=False,
    #             question_count=0
    #         )
    #         db.add(f)
    #         added += 1
    #     else:
    #         if desc and existing.description != desc:
    #             existing.description = desc
    #             existing.is_modified = True
    #             db.add(existing)
    #             updated += 1
    #         else:
    #             skipped += 1

    # db.commit()
    # return {"added": added, "updated": updated, "skipped": skipped}



# def get_unindexed_questions(db):
#     rows = (
#         db.query(Question, Feature)
#         .join(Feature, Feature.id == Question.feature_id)
#         .filter(Question.status == 2, Question.is_indexed == False)
#         .all()
#     )

#     if not rows:
#         return []

#     return [
#         {
#             "id": q.Question.id,
#             "feature_name": q.Feature.name,
#             "question": q.Question.question,
#             "answer": q.Question.answer
#         }
#         for q in rows
#     ]


# def mark_questions_indexed(db, question_ids):
#     if not question_ids:
#         raise_api_error("VALIDATION_ERROR", "question_ids missing or empty", 400)

#     db.query(Question).filter(Question.id.in_(question_ids)).update(
#         {"is_indexed": True}, synchronize_session=False
#     )
#     db.commit()
#     return {"updated": len(question_ids)}



def search_similar_questions(feature_id: int, question_text: str, feature_name: str,
                             page: int = 1, limit: int = 10) -> dict:

    if not RETRIEVER_URL:
        raise_api_error("INTERNAL_ERROR", "Retriever service URL not configured", 500)

    if not question_text or len(question_text.strip()) < 3:
        raise_api_error("SIMILARITY_MIN_LENGTH", "Question text too short for similarity search", 400)

    key_raw = f"{feature_id}:{question_text.strip().lower()}"
    cache_key = f"similar:{hashlib.md5(key_raw.encode('utf-8')).hexdigest()}"
    print(f"[CacheCheck] key={cache_key}")

    cached_data = redis_client.get(cache_key)
    if cached_data:
        print(f"[CacheHit] {cache_key}")
        try:
            merged_results = json.loads(cached_data)
        except Exception:
            redis_client.delete(cache_key)
            print(f"[CacheCorrupt] Deleted invalid cache for {cache_key}")
            merged_results = []
    else:
        print(f"[CacheMiss] {cache_key} — Fetching from retriever")
        from config import API_SERVER_URL
        encoded_query = quote_plus(f"{feature_name} {question_text}")
        url = f"{API_SERVER_URL}/kc_admin/similar-search"
        payload = {"query": f"{feature_name} {question_text}"}

        try:
            with httpx.Client(timeout=100.0) as client:
                resp = client.post(url, json=payload)
        except httpx.RequestError as e:
            raise_api_error("INTERNAL_ERROR", f"API Server unreachable: {e}", 500)

        if resp.status_code != 200:
            raise_api_error("INTERNAL_ERROR", f"API Server error ({resp.status_code})", 500)

        data = resp.json().get("data", {})
        print(f"[RetrieverResponse] {json.dumps(data, indent=2)[:500]}")
        if "top_matches" in data:
            top_matches = data["top_matches"]
        elif isinstance(data.get("results"), dict):
            top_matches = data["results"].get("top_matches", [])
        else:
            top_matches = []

        all_feature_questions = data.get("all_feature_questions", [])
        def normalize(items):
            return [
                {
                    "id": item.get("id"),
                    "question": item.get("question"),
                    "answer": item.get("answer")
                }
                for item in items if item.get("question")
            ]

        normalized_top = normalize(top_matches)
        normalized_all = normalize(all_feature_questions)
        top_ids = {item["id"] for item in normalized_top}
        filtered_all = [item for item in normalized_all if item["id"] not in top_ids]
        merged_results = normalized_top + filtered_all
        redis_client.setex(cache_key, 600, json.dumps(merged_results))
        print(f"[CacheSet] Stored {len(merged_results)} merged results for {cache_key}")
    total_items = len(merged_results)
    total_pages = max(1, (total_items + limit - 1) // limit)

    if page < 1 or page > total_pages:
        raise_api_error("PAGINATION_OUT_OF_RANGE", "Page number out of range", 400)

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = merged_results[start_idx:end_idx]

    pagination = {
        "current_page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "items_per_page": limit,
    }

    print(f"[FinalResponse] Returning {len(paginated_items)} items out of {total_items}")
    return {"items": paginated_items, "pagination": pagination}


def get_feature_with_questions(db: Session, feature_id: int) -> dict:
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    import json
    desc_str = json.dumps(f.description) if f.description is not None else None

    questions = (
        db.query(Question)
        .filter(Question.feature_id == feature_id)
        .order_by(Question.id.asc())
        .all()
    )

    question_list = [
        {
            "id": q.id,
            "feature_id": q.feature_id,
            "question": q.question,
            "answer": q.answer,
            "status": q.status,
            "created_at": q.created_at,
            "updated_at": q.updated_at,
        }
        for q in questions
    ]

    return {
        "id": f.id,
        "name": f.name,
        "description": desc_str,
        "question_count": f.question_count,
        "is_modified": f.is_modified,
        "created_at": f.created_at,
        "updated_at": f.updated_at,
        "questions": question_list,
    }


def delete_feature(db: Session, feature_id: int) -> dict:
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    # Fetch all question IDs for response before deletion
    questions = db.query(Question).filter(Question.feature_id == feature_id).all()
    deleted_question_ids = [q.id for q in questions]

    # Cascade delete handled automatically by FK, but delete manually for clarity
    for q in questions:
        db.delete(q)
    db.delete(f)
    db.commit()

    return {
        "deleted_feature_id": feature_id,
        "deleted_question_ids": deleted_question_ids,
    }

def move_final_to_draft(db: Session, feature_id: int, question_id: int) -> dict:
    # Find the feature and question
    f = db.query(Feature).filter(Feature.id == feature_id).first()
    if not f:
        raise_api_error("FEATURE_NOT_FOUND", "Feature not found", 404)

    q = db.query(Question).filter(
        Question.feature_id == feature_id, Question.id == question_id
    ).first()
    if not q:
        raise_api_error("QUESTION_NOT_FOUND", "Question not found", 404)

    # Only allow moving if it's final
    if q.status != 2:
        raise_api_error("VALIDATION_ERROR", "Only final questions can be moved to draft", 400)

    # Create a new draft copy
    new_q = Question(
        feature_id=q.feature_id,
        question=q.question,
        answer=q.answer,
        status=1,  # draft
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)

    # Return full response with original info
    return {
        "id": new_q.id,
        "feature_id": new_q.feature_id,
        "question": new_q.question,
        "answer": new_q.answer,
        "status": new_q.status,
        "original_question": q.question,
        "original_answer": q.answer,
        "original_status": q.status,
    }
