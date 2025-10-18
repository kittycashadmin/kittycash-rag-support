# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

from fastapi import APIRouter, Depends
from typing import Any
from sqlalchemy.orm import Session
from db import get_db
import crud, schemas
from error_responses import raise_api_error

#router = APIRouter(prefix="/admin/kc_feature_faq/features", tags=["features"])
router = APIRouter(prefix="/admin/kc_feature_faq/features", tags=["features"])

@router.get("", response_model=schemas.FeatureListResp)
def api_list_features(db: Session = Depends(get_db)):
    features = crud.list_features(db)
    return {"features": features}

@router.get("/{feature_id}")
def api_get_feature(feature_id: int, db: Session = Depends(get_db)):
    feature_data = crud.get_feature_with_questions(db, feature_id)
    return {"success": True, "data": feature_data}



@router.post("", response_model=schemas.FeatureResponse)
def api_create_feature(payload: schemas.FeatureCreate, db: Session = Depends(get_db)):
    f = crud.create_feature(db, name=payload.name, description_str=payload.description)
    import json
    desc_str = json.dumps(f.description) if f.description is not None else None
    return {
        "id": f.id,
        "name": f.name,
        "description": desc_str,
        "question_count": f.question_count,
        "is_modified": f.is_modified,
        "created_at": f.created_at,
        "updated_at": f.updated_at
    }

@router.put("/{feature_id}", response_model=schemas.FeatureResponse)
def api_update_feature(feature_id: int, payload: schemas.FeatureUpdate, db: Session = Depends(get_db)):
    f = crud.update_feature(db, feature_id=feature_id, description_str=payload.description)
    import json
    desc_str = json.dumps(f.description) if f.description is not None else None
    return {
        "id": f.id,
        "name": f.name,
        "description": desc_str,
        "question_count": f.question_count,
        "is_modified": f.is_modified,
        "created_at": f.created_at,
        "updated_at": f.updated_at
    }

@router.post("/{feature_id}/similar-questions/search") # only questions
def api_similar_search(feature_id: int, payload: schemas.SimilarSearchRequest, db: Session = Depends(get_db)):
    feature = crud.get_feature(db, feature_id)
    res = crud.search_similar_questions(
        feature_id=feature_id,
        question_text=payload.question,
        feature_name=feature.name,  
        page=payload.page or 1,
        limit=payload.limit or 10
    )
    return {"success": True, "data": res}


@router.post("/{feature_id}/delete")
def api_delete_feature(feature_id: int, db: Session = Depends(get_db)):
    res = crud.delete_feature(db, feature_id)
    return {"success": True, "data": res}


