# src/kajibalance/data.py
# タスクマスター・割り当て・感謝ポイントのJSON永続化

from pathlib import Path
from pydantic import TypeAdapter
import json
import uuid
from datetime import date
from .models import Task, TaskAssignment, GratitudePoint, PairConfig

DATA_DIR = Path(__file__).parent.parent.parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"
ASSIGN_FILE = DATA_DIR / "assignments.json"
GRAT_FILE = DATA_DIR / "gratitudes.json"
PAIR_FILE = DATA_DIR / "pair.json"


def _read_json(path: str) -> list | dict:
    if not Path(path).exists():
        return []
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, data: list | dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def load_tasks() -> list[Task]:
    raw = _read_json(str(TASKS_FILE))
    if not raw:
        return get_initial_tasks()
    return TypeAdapter(list[Task]).validate_python(raw)


def save_tasks(tasks: list[Task]) -> None:
    _write_json(str(TASKS_FILE), TypeAdapter(list[Task]).dump_python(tasks))


def load_assignments() -> list[TaskAssignment]:
    raw = _read_json(str(ASSIGN_FILE))
    if not raw:
        return []
    return TypeAdapter(list[TaskAssignment]).validate_python(raw)


def save_assignments(assignments: list[TaskAssignment]) -> None:
    _write_json(str(ASSIGN_FILE), TypeAdapter(list[TaskAssignment]).dump_python(assignments))


def load_gratitudes() -> list[GratitudePoint]:
    raw = _read_json(str(GRAT_FILE))
    if not raw:
        return []
    return TypeAdapter(list[GratitudePoint]).validate_python(raw)


def save_gratitudes(gratitudes: list[GratitudePoint]) -> None:
    _write_json(str(GRAT_FILE), TypeAdapter(list[GratitudePoint]).dump_python(gratitudes))


def load_pair() -> PairConfig:
    raw = _read_json(str(PAIR_FILE))
    if isinstance(raw, dict):
        return PairConfig(**raw)
    return PairConfig()


def save_pair(pair: PairConfig) -> None:
    _write_json(str(PAIR_FILE), pair.model_dump())


def create_assignment(task_id: str, assignee_id: str) -> TaskAssignment:
    return TaskAssignment(
        id=str(uuid.uuid4())[:8],
        pair_id="default",
        task_id=task_id,
        assignee_id=assignee_id,
        due_date=date.today(),
    )


def get_next_id(tasks: list[Task]) -> str:
    return str(max(int(t.id) for t in tasks) + 1)


def get_initial_tasks() -> list[Task]:
    rows = [
        (1,"夕飯の献立を考える","料理",1,9,"daily"),
        (2,"夕飯を作る","料理",7,4,"daily"),
        (3,"食器を洗う","料理",6,1,"daily"),
        (4,"食材の買い出し","買い物",5,4,"weekly"),
        (5,"洗濯（干す）","掃除",4,2,"weekly"),
        (6,"洗濯（たたむ）","掃除",3,1,"weekly"),
        (7,"部屋の掃除機","掃除",5,2,"weekly"),
        (8,"保育園の準備","育児",1,7,"daily"),
        (9,"子どもの歯磨き","育児",3,4,"daily"),
        (10,"ゴミ出し","掃除",3,2,"weekly"),
        (11,"風呂掃除","掃除",5,1,"weekly"),
        (12,"トイレ掃除","掃除",4,1,"weekly"),
        (13,"ベッドメイキング","掃除",2,1,"daily"),
        (14,"キッチン掃除","掃除",4,2,"weekly"),
        (15,"窓拭き","掃除",5,2,"monthly"),
        (16,"洗濯物を取り込む","掃除",2,1,"daily"),
        (17,"アイロンがけ","掃除",3,1,"irregular"),
        (18,"布団を干す","掃除",4,1,"weekly"),
        (19,"朝食の準備","料理",4,3,"daily"),
        (20,"昼食の準備","料理",4,3,"daily"),
        (21,"夕食の片付け","料理",4,2,"daily"),
        (22,"お弁当作り","料理",3,5,"daily"),
        (23,"冷蔵庫の整理","料理",2,3,"weekly"),
        (24,"調味料の補充","料理",2,3,"weekly"),
        (25,"食材の在庫確認","買い物",1,4,"weekly"),
        (26,"日用品の買い出し","買い物",4,3,"weekly"),
        (27,"ネットショッピング","買い物",1,3,"irregular"),
        (28,"子どもの送り迎え","育児",3,4,"daily"),
        (29,"保育園の準備物チェック","育児",1,6,"daily"),
        (30,"子どもの寝かしつけ","育児",3,4,"daily"),
        (31,"子どもの入浴","育児",5,3,"daily"),
        (32,"宿題を見る","育児",1,4,"daily"),
        (33,"学校行事の確認","育児",1,6,"irregular"),
        (34,"子どもの服の買い替え","育児",2,4,"monthly"),
        (35,"予防接種・健診の予約","育児",1,7,"irregular"),
        (36,"ペットの餌やり","ペット",2,3,"daily"),
        (37,"ペットの散歩","ペット",6,2,"daily"),
        (38,"ペットのトイレ掃除","ペット",4,2,"daily"),
        (39,"ペットの病院連れて行く","ペット",4,6,"irregular"),
        (40,"薬の管理","手続き",1,6,"daily"),
        (41,"郵便物の処理","手続き",1,4,"weekly"),
        (42,"役所の手続き","手続き",1,5,"irregular"),
        (43,"家計簿・お金の管理","手続き",1,7,"weekly"),
        (44,"保険の見直し","手続き",1,5,"irregular"),
        (45,"病院の予約・管理","手続き",1,5,"irregular"),
        (46,"予定の調整（親戚・友人）","手続き",1,5,"irregular"),
        (47,"家具の配置替え","その他",6,2,"irregular"),
        (48,"不用品の整理","その他",4,3,"irregular"),
        (49,"観葉植物の世話","その他",2,1,"weekly"),
        (50,"ゴミの分別ルール確認","その他",1,3,"weekly"),
    ]
    return [Task(id=str(r[0]), name=r[1], category=r[2], physical_score=r[3], mental_score=r[4], default_frequency=r[5], sort_order=r[0]) for r in rows]
