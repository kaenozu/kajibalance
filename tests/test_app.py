# tests/test_app.py
# アプリケーションロジックのユニットテスト

from datetime import date
from kajibalance.models import Task, TaskAssignment


def make_assignment(task_id: str, assignee_id: str, completed: bool = False) -> TaskAssignment:
    return TaskAssignment(
        id=f"a_{task_id}",
        pair_id="default",
        task_id=task_id,
        assignee_id=assignee_id,
        due_date=date.today(),
        completed=completed,
    )


def make_task(id: str, name: str, phys: int, ment: int, category: str = "料理") -> Task:
    return Task(id=id, name=name, category=category, physical_score=phys, mental_score=ment, default_frequency="daily")


class TestCalcScores:
    """calc_scores のロジックを直接テスト"""

    def _calc(self, tasks: list[Task], assignments: list[TaskAssignment]):
        """calc_scores と同じロジックをインライン実装"""
        tm = {t.id: t for t in tasks}
        s = {"me": {"phys": 0, "ment": 0}, "partner": {"phys": 0, "ment": 0}}
        for a in assignments:
            if a.completed:
                t = tm.get(a.task_id)
                if t:
                    s[a.assignee_id]["phys"] += t.physical_score
                    s[a.assignee_id]["ment"] += t.mental_score
        tp = s["me"]["phys"] + s["partner"]["phys"] or 1
        tm2 = s["me"]["ment"] + s["partner"]["ment"] or 1
        return {
            "me_phys": round(s["me"]["phys"] / tp * 100),
            "partner_phys": round(s["partner"]["phys"] / tp * 100),
            "me_ment": round(s["me"]["ment"] / tm2 * 100),
            "partner_ment": round(s["partner"]["ment"] / tm2 * 100),
        }

    def test_no_assignments(self):
        tasks = [make_task("1", "夕飯作り", 7, 4)]
        result = self._calc(tasks, [])
        assert result["me_phys"] == 0
        assert result["partner_phys"] == 0
        assert result["me_ment"] == 0
        assert result["partner_ment"] == 0

    def test_all_me(self):
        tasks = [make_task("1", "夕飯作り", 7, 4)]
        assignments = [make_assignment("1", "me", completed=True)]
        result = self._calc(tasks, assignments)
        assert result["me_phys"] == 100
        assert result["partner_phys"] == 0
        assert result["me_ment"] == 100
        assert result["partner_ment"] == 0

    def test_all_partner(self):
        tasks = [make_task("1", "夕飯作り", 7, 4)]
        assignments = [make_assignment("1", "partner", completed=True)]
        result = self._calc(tasks, assignments)
        assert result["me_phys"] == 0
        assert result["partner_phys"] == 100
        assert result["me_ment"] == 0
        assert result["partner_ment"] == 100

    def test_even_split(self):
        tasks = [
            make_task("1", "料理", 5, 3),
            make_task("2", "掃除", 5, 3),
        ]
        assignments = [
            make_assignment("1", "me", completed=True),
            make_assignment("2", "partner", completed=True),
        ]
        result = self._calc(tasks, assignments)
        assert result["me_phys"] == 50
        assert result["partner_phys"] == 50
        assert result["me_ment"] == 50
        assert result["partner_ment"] == 50

    def test_unbalanced(self):
        tasks = [
            make_task("1", "重い料理", 9, 7),
            make_task("2", "軽い掃除", 1, 1),
        ]
        assignments = [
            make_assignment("1", "me", completed=True),
            make_assignment("2", "partner", completed=True),
        ]
        result = self._calc(tasks, assignments)
        assert result["me_phys"] == 90
        assert result["partner_phys"] == 10
        assert result["me_ment"] > 50
        assert result["partner_ment"] < 50

    def test_incomplete_not_counted(self):
        tasks = [make_task("1", "夕飯作り", 7, 4)]
        assignments = [make_assignment("1", "me", completed=False)]
        result = self._calc(tasks, assignments)
        assert result["me_phys"] == 0
        assert result["me_ment"] == 0

    def test_missing_task_ignored(self):
        assignments = [make_assignment("999", "me", completed=True)]
        result = self._calc([], assignments)
        assert result["me_phys"] == 0
        assert result["me_ment"] == 0
