# src/kajibalance/models.py
# データモデル定義
# Pydanticで型安全なデータ構造を提供

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


Category = Literal["料理", "掃除", "買い物", "育児", "ペット", "手続き", "その他"]
Frequency = Literal["daily", "weekly", "monthly", "irregular"]


class Task(BaseModel):
    id: str
    name: str
    category: Category
    physical_score: int = Field(ge=1, le=10)
    mental_score: int = Field(ge=1, le=10)
    default_frequency: Frequency
    sort_order: int | None = None
    is_active: bool = True


class TaskAssignment(BaseModel):
    id: str
    pair_id: str
    task_id: str
    assignee_id: str
    due_date: date
    completed: bool = False
    completed_at: datetime | None = None


class GratitudePoint(BaseModel):
    id: str
    from_id: str
    to_id: str
    task_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class PairConfig(BaseModel):
    my_name: str = "あなた"
    partner_name: str = "パートナー"
    invite_code: str = ""
    paired: bool = False
