# src/app/db/models.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeDimension(Base):
    __tablename__ = "knowledge_dimension"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 1=简答 2=教学设计
    question_type: Mapped[int] = mapped_column(Integer)
    # 1=初 2=中 3=高
    difficulty: Mapped[int] = mapped_column(Integer)

    title: Mapped[str] = mapped_column(Text)
    material: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    score: Mapped[int] = mapped_column(Integer, default=10)
    suggest_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    word_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 历史兼容字段：可保留为 JSONB
    knowledge_ids: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # 核心知识点（数组）
    score_points: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    answer_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scoring_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class QuestionKdRelation(Base):
    __tablename__ = "question_kd_relation"

    q_id: Mapped[int] = mapped_column(ForeignKey("question.id"), primary_key=True)
    kd_id: Mapped[int] = mapped_column(ForeignKey("knowledge_dimension.id"), primary_key=True)


class AnswerRecord(Base):
    __tablename__ = "answer_record"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    q_id: Mapped[int] = mapped_column(ForeignKey("question.id"))

    # 1=文本 2=附件 3=自动
    answer_type: Mapped[int] = mapped_column(Integer, default=1)

    original_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submit_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    total_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    subitem_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    dimension_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hit_score_points: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
