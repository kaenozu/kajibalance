# tests/test_models.py
# Pydanticモデルのユニットテスト

from datetime import date, datetime
import pytest
from pydantic import ValidationError
from kajibalance.models import Task, TaskAssignment, GratitudePoint, PairConfig


class TestTask:
    def test_create_valid(self):
        t = Task(id="1", name="テスト", category="料理", physical_score=5, mental_score=3, default_frequency="daily")
        assert t.id == "1"
        assert t.name == "テスト"
        assert t.category == "料理"
        assert t.physical_score == 5
        assert t.mental_score == 3
        assert t.default_frequency == "daily"
        assert t.sort_order is None
        assert t.is_active is True

    def test_create_minimal(self):
        t = Task(id="2", name="最小", category="掃除", physical_score=1, mental_score=1, default_frequency="irregular")
        assert t.sort_order is None
        assert t.is_active is True

    def test_physical_score_out_of_range(self):
        with pytest.raises(ValidationError):
            Task(id="3", name="NG", category="料理", physical_score=0, mental_score=1, default_frequency="daily")

    def test_physical_score_too_high(self):
        with pytest.raises(ValidationError):
            Task(id="4", name="NG", category="料理", physical_score=11, mental_score=1, default_frequency="daily")

    def test_mental_score_out_of_range(self):
        with pytest.raises(ValidationError):
            Task(id="5", name="NG", category="料理", physical_score=1, mental_score=0, default_frequency="daily")

    def test_invalid_category(self):
        with pytest.raises(ValidationError):
            Task(id="6", name="NG", category="無効カテゴリ", physical_score=1, mental_score=1, default_frequency="daily")

    def test_invalid_frequency(self):
        with pytest.raises(ValidationError):
            Task(id="7", name="NG", category="料理", physical_score=1, mental_score=1, default_frequency="yearly")

    def test_all_categories(self):
        for cat in ["料理", "掃除", "買い物", "育児", "ペット", "手続き", "その他"]:
            Task(id="x", name="cat", category=cat, physical_score=1, mental_score=1, default_frequency="daily")

    def test_all_frequencies(self):
        for freq in ["daily", "weekly", "monthly", "irregular"]:
            Task(id="x", name="freq", category="料理", physical_score=1, mental_score=1, default_frequency=freq)

    def test_with_sort_order(self):
        t = Task(id="10", name="並び替え", category="その他", physical_score=2, mental_score=2, default_frequency="monthly", sort_order=5)
        assert t.sort_order == 5

    def test_with_is_active_false(self):
        t = Task(id="11", name="非活性", category="買い物", physical_score=3, mental_score=3, default_frequency="weekly", is_active=False)
        assert t.is_active is False


class TestTaskAssignment:
    def test_create_valid(self):
        a = TaskAssignment(id="a1", pair_id="default", task_id="1", assignee_id="me", due_date=date(2026, 6, 1))
        assert a.id == "a1"
        assert a.completed is False
        assert a.completed_at is None

    def test_with_completed(self):
        from datetime import datetime
        dt = datetime(2026, 6, 1, 12, 0, 0)
        a = TaskAssignment(id="a2", pair_id="default", task_id="1", assignee_id="partner", due_date=date(2026, 6, 1), completed=True, completed_at=dt)
        assert a.completed is True
        assert a.completed_at == dt


class TestGratitudePoint:
    def test_create_valid(self):
        g = GratitudePoint(id="g1", from_id="me", to_id="partner")
        assert g.task_id is None
        assert isinstance(g.created_at, datetime)

    def test_with_task_id(self):
        g = GratitudePoint(id="g2", from_id="partner", to_id="me", task_id="1")
        assert g.task_id == "1"

    def test_created_at_default(self):
        g1 = GratitudePoint(id="g3", from_id="me", to_id="partner")
        g2 = GratitudePoint(id="g4", from_id="me", to_id="partner")
        assert g1.created_at <= g2.created_at


class TestPairConfig:
    def test_defaults(self):
        p = PairConfig()
        assert p.my_name == "あなた"
        assert p.partner_name == "パートナー"
        assert p.invite_code == ""
        assert p.paired is False

    def test_custom_values(self):
        p = PairConfig(my_name="太郎", partner_name="花子", invite_code="ABC123", paired=True)
        assert p.my_name == "太郎"
        assert p.partner_name == "花子"
        assert p.invite_code == "ABC123"
        assert p.paired is True
