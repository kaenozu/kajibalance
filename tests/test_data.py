# tests/test_data.py
# データ永続化のユニットテスト

from datetime import date
from kajibalance.data import (
    get_initial_tasks, get_next_id, create_assignment,
    _read_json, _write_json,
    load_tasks, save_tasks,
    load_assignments, save_assignments,
    load_gratitudes, save_gratitudes,
    load_pair, save_pair,
)
from kajibalance.models import Task, GratitudePoint, PairConfig


class TestGetInitialTasks:
    def test_returns_50_tasks(self):
        tasks = get_initial_tasks()
        assert len(tasks) == 50

    def test_all_have_valid_fields(self):
        tasks = get_initial_tasks()
        for t in tasks:
            assert isinstance(t.id, str) and t.id.isdigit()
            assert isinstance(t.name, str) and len(t.name) > 0
            assert t.category in ("料理", "掃除", "買い物", "育児", "ペット", "手続き", "その他")
            assert 1 <= t.physical_score <= 10
            assert 1 <= t.mental_score <= 10
            assert t.default_frequency in ("daily", "weekly", "monthly", "irregular")
            assert t.sort_order == int(t.id)

    def test_ids_sequential(self):
        tasks = get_initial_tasks()
        ids = [int(t.id) for t in tasks]
        assert ids == list(range(1, 51))

    def test_scores_vary(self):
        tasks = get_initial_tasks()
        phys_scores = [t.physical_score for t in tasks]
        ment_scores = [t.mental_score for t in tasks]
        assert max(phys_scores) >= 5
        assert max(ment_scores) >= 5


class TestGetNextId:
    def test_next_id(self):
        tasks = get_initial_tasks()
        assert get_next_id(tasks) == "51"

    def test_with_empty_list(self):
        tasks = [Task(id="5", name="x", category="料理", physical_score=1, mental_score=1, default_frequency="daily")]
        assert get_next_id(tasks) == "6"


class TestCreateAssignment:
    def test_creates_assignment(self):
        a = create_assignment("1", "me")
        assert a.task_id == "1"
        assert a.assignee_id == "me"
        assert a.pair_id == "default"
        assert a.due_date == date.today()
        assert a.completed is False
        assert len(a.id) == 8

    def test_different_assignee(self):
        a = create_assignment("2", "partner")
        assert a.assignee_id == "partner"


class TestJsonRoundtrip:
    def test_read_write_json(self, tmp_path):
        path = str(tmp_path / "test.json")
        data = [{"key": "value"}]
        _write_json(path, data)
        result = _read_json(path)
        assert result == data

    def test_read_nonexistent(self, tmp_path):
        result = _read_json(str(tmp_path / "nonexistent.json"))
        assert result == []


class TestTasksPersistence:
    def test_save_and_load_tasks(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.TASKS_FILE", tmp_path / "tasks.json")
        tasks = get_initial_tasks()
        save_tasks(tasks)
        loaded = load_tasks()
        assert len(loaded) == 50
        assert loaded[0].name == "夕飯の献立を考える"

    def test_load_tasks_empty_returns_default(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.TASKS_FILE", tmp_path / "tasks.json")
        # File doesn't exist yet
        loaded = load_tasks()
        assert len(loaded) == 50  # Falls back to initial tasks


class TestAssignmentsPersistence:
    def test_save_and_load_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.ASSIGN_FILE", tmp_path / "assignments.json")
        save_assignments([])
        loaded = load_assignments()
        assert loaded == []

    def test_save_and_load_with_data(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.ASSIGN_FILE", tmp_path / "assignments.json")
        assignments = [create_assignment("1", "me")]
        save_assignments(assignments)
        loaded = load_assignments()
        assert len(loaded) == 1
        assert loaded[0].task_id == "1"

    def test_load_empty_returns_empty_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.ASSIGN_FILE", tmp_path / "nonexistent.json")
        loaded = load_assignments()
        assert loaded == []


class TestGratitudesPersistence:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.GRAT_FILE", tmp_path / "gratitudes.json")
        gratitudes = [GratitudePoint(id="g1", from_id="me", to_id="partner")]
        save_gratitudes(gratitudes)
        loaded = load_gratitudes()
        assert len(loaded) == 1
        assert loaded[0].from_id == "me"

    def test_load_empty(self, tmp_path, monkeypatch):
        loaded = load_gratitudes()
        assert loaded == []


class TestPairPersistence:
    def test_save_and_load_default(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.PAIR_FILE", tmp_path / "pair.json")
        pair = PairConfig()
        save_pair(pair)
        loaded = load_pair()
        assert loaded.my_name == "あなた"
        assert loaded.paired is False

    def test_save_and_load_custom(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.PAIR_FILE", tmp_path / "pair.json")
        pair = PairConfig(my_name="太郎", partner_name="花子", paired=True)
        save_pair(pair)
        loaded = load_pair()
        assert loaded.my_name == "太郎"
        assert loaded.paired is True

    def test_load_nonexistent_returns_default(self, tmp_path, monkeypatch):
        monkeypatch.setattr("kajibalance.data.PAIR_FILE", tmp_path / "nonexistent.json")
        loaded = load_pair()
        assert isinstance(loaded, PairConfig)
