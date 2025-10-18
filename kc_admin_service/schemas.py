from typing import Optional, List, Any, Dict
from pydantic import BaseModel, validator
from datetime import datetime
import json

class FeatureBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None  

    @validator("name")
    def name_len(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name required")
        if len(v) > 120:
            raise ValueError("name must be <= 120 characters")
        return v

    @validator("description")
    def description_json_valid(cls, v):
        if v is None:
            return v
        try:
            parsed = json.loads(v)
        except Exception:
            raise ValueError("description must be a valid JSON string (Quill Delta array)")
        if not isinstance(parsed, (list, dict)):
            raise ValueError("description must be a JSON array/object representing a Quill Delta")
        return v

class FeatureCreate(FeatureBase):
    name: str
    description: Optional[str] = None

class FeatureUpdate(BaseModel):
    description: Optional[str] = None

    @validator("description")
    def description_json_valid(cls, v):
        if v is None:
            return v
        import json
        try:
            parsed = json.loads(v)
        except Exception:
            raise ValueError("description must be a valid JSON string (Quill Delta array)")
        if not isinstance(parsed, (list, dict)):
            raise ValueError("description must be a JSON array/object representing a Quill Delta")
        return v

class FeatureResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None 
    question_count: int
    is_modified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class FeatureListResp(BaseModel):
    features: List[Dict[str, Any]]

class QuestionBase(BaseModel):
    question: str
    answer: str

    @validator("question", "answer")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None

    @validator("question", "answer")
    def not_empty_optional(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

class QuestionResponse(BaseModel):
    id: int
    feature_id: int
    question: str
    answer: str
    status: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SimilarSearchRequest(BaseModel):
    question: str
    answer: Optional[str] = None
    page: Optional[int] = 1
    limit: Optional[int] = 10
    feature_name: Optional[str] = None

    @validator("question")
    def min_length(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("Question text too short for similarity search (min 3 chars)")
        return v.strip()


class FeatureDeleteResponse(BaseModel):
    deleted_feature_id: int
    deleted_question_ids: List[int]

class QuestionDeleteResponse(BaseModel):
    deleted_ids: List[int]
    restored_ids: List[int]
    failed_ids: List[int]
