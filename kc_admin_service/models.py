from sqlalchemy import Column, BigInteger, String, Boolean, Integer, Text, SmallInteger, DateTime, func, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from db import Base

class Feature(Base):
    __tablename__ = "ai_chat_features"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(JSONB, nullable=True)  
    is_modified = Column(Boolean, nullable=False, default=False)
    question_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)



class Question(Base):
    __tablename__ = "ai_chat_questions"

    id = Column(BigInteger, primary_key=True, index=True)
    feature_id = Column(BigInteger, ForeignKey("ai_chat_features.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    status = Column(SmallInteger, nullable=False, default=1)  
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_indexed = Column(Boolean, nullable=False, default=False)



