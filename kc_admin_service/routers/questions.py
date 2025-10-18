# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db import get_db
import crud, schemas

#router = APIRouter(prefix="/admin/ai-chat/features", tags=["questions"])
router = APIRouter(prefix="/admin/kc_feature_faq/features", tags=["questions"])


@router.get("/{feature_id}/questions")
def api_list_questions(feature_id: int, status: int = None, db: Session = Depends(get_db)):
    res = crud.list_questions(db, feature_id=feature_id, status=status)
    return {"success": True, "data": res}

@router.post("/{feature_id}/questions")
def api_create_question(feature_id: int, payload: schemas.QuestionCreate, db: Session = Depends(get_db)):
    q = crud.create_question(db, feature_id=feature_id, question_text=payload.question, answer_text=payload.answer)
    return {"success": True, "data": {
        "id": q.id, "feature_id": q.feature_id, "question": q.question, "answer": q.answer, "status": q.status, "created_at": q.created_at, "updated_at": q.updated_at
    }}

@router.put("/{feature_id}/questions/{question_id}")
def api_update_question(feature_id: int, question_id: int, payload: schemas.QuestionUpdate, db: Session = Depends(get_db)):
    q = crud.update_question(db, feature_id=feature_id, question_id=question_id, question_text=payload.question, answer_text=payload.answer)
    return {"success": True, "data": {
        "id": q.id, "feature_id": q.feature_id, "question": q.question, "answer": q.answer, "status": q.status, "created_at": q.created_at, "updated_at": q.updated_at
    }}

@router.post("/{feature_id}/questions/submit")
def api_submit_questions(feature_id: int, body: dict, db: Session = Depends(get_db)):
    question_ids = body.get("question_ids")
    if not isinstance(question_ids, list):
        raise crud.raise_api_error("VALIDATION_ERROR", "question_ids must be an array", 400)
    res = crud.submit_questions(db, feature_id=feature_id, question_ids=question_ids)
    return {"success": True, "data": res}

@router.post("/{feature_id}/questions/delete")
def api_delete_questions(feature_id: int, body: dict, db: Session = Depends(get_db)):
    question_ids = body.get("question_ids")
    if not isinstance(question_ids, list):
        raise crud.raise_api_error("VALIDATION_ERROR", "question_ids must be an array", 400)
    res = crud.delete_questions(db, feature_id=feature_id, question_ids=question_ids)
    return {"success": True, "data": res}


# @router.get("/unindexed")
# def api_get_unindexed_questions(db: Session = Depends(get_db)):
#     res = crud.get_unindexed_questions(db)
#     return {"success": True, "data": res}


# @router.post("/mark-indexed")
# def api_mark_indexed_questions(body: dict, db: Session = Depends(get_db)):
#     question_ids = body.get("question_ids")
#     res = crud.mark_questions_indexed(db, question_ids)
#     return {"success": True, "data": res}

@router.post("/{feature_id}/questions/{question_id}/move-to-draft")
def api_move_final_to_draft(feature_id: int, question_id: int, db: Session = Depends(get_db)):
    res = crud.move_final_to_draft(db, feature_id, question_id)
    return {"success": True, "data": res}
