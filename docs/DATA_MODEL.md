# KajiBalance データモデル設計

## 1. 概要

Phase 1（Glide + Google Sheets）のデータ構造を示す。
Phase 2（Firebase移行時）の想定も併記する。

---

## 2. Phase 1: Google Sheets テーブル定義

### 2.1 テーブル一覧

| シート名 | 用途 | 主なカラム |
|---|---|---|
| `users` | ユーザー情報 | id, name, email, pair_code, partner_id |
| `tasks` | タスクマスター | id, name, category, physical_score, mental_score, default_frequency |
| `task_assignments` | タスク割り当て実績 | id, task_id, assignee_id, date, completed, completed_at |
| `gratitude_points` | 感謝ポイント | id, from_id, to_id, task_assignment_id, created_at |
| `templates` | テンプレート定義 | id, name, task_ids_json, description |

---

### 2.2 各シート詳細

#### users

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| id | TEXT | ○ | 自動生成UUID |
| name | TEXT | ○ | 表示名 |
| email | TEXT | ○ | ログイン用メール |
| password_hash | TEXT | ○ | ハッシュ化パスワード |
| pair_code | TEXT | △ | ペア招待コード（初回生成） |
| partner_id | TEXT | △ | ペア相手のuser_id |
| plan | TEXT | ○ | "free" or "premium" |
| privacy_policy_version | TEXT | ○ | 同意したプライバシーポリシーのバージョン |
| terms_accepted_at | TIMESTAMP | ○ | 利用規約同意日時 |
| created_at | TIMESTAMP | ○ | - |
| updated_at | TIMESTAMP | ○ | - |

#### tasks

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| id | TEXT | ○ | 自動生成UUID |
| name | TEXT | ○ | タスク名（例：「夕飯の献立を考える」） |
| category | TEXT | ○ | 料理/掃除/買い物/育児/ペット/手続き/その他 |
| physical_score | INTEGER | ○ | 1〜10 身体的負担 |
| mental_score | INTEGER | ○ | 1〜10 精神的負担 |
| default_frequency | TEXT | ○ | "daily"/"weekly"/"monthly"/"irregular" |
| sort_order | INTEGER | △ | 表示順 |
| is_active | BOOLEAN | ○ | デフォルトtrue |

#### task_assignments

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| id | TEXT | ○ | 自動生成UUID |
| pair_id | TEXT | ○ | ペア識別子（両ユーザー共通） |
| task_id | TEXT | ○ | tasks.id |
| assignee_id | TEXT | ○ | 担当者 users.id |
| due_date | DATE | ○ | 予定日 |
| completed | BOOLEAN | ○ | 完了フラグ |
| completed_at | TIMESTAMP | △ | 完了日時 |
| note | TEXT | △ | メモ |
| created_at | TIMESTAMP | ○ | - |

#### gratitude_points

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| id | TEXT | ○ | 自動生成UUID |
| from_id | TEXT | ○ | 送り主 users.id |
| to_id | TEXT | ○ | 受け取り手 users.id |
| task_assignment_id | TEXT | △ | 紐づくタスク実績 |
| message | TEXT | △ | 任意メッセージ |
| created_at | TIMESTAMP | ○ | - |

#### templates

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| id | TEXT | ○ | 自動生成UUID |
| name | TEXT | ○ | テンプレート名（新婚向け/子育て向け/同棲向け） |
| description | TEXT | △ | 説明 |
| task_ids_json | TEXT | ○ | タスクID配列のJSON |
| suggested_ratios | TEXT | △ | 推奨担当比率のJSON |

---

## 3. Phase 2: Firebase Firestore 移行時

### 3.1 コレクション構成

```
/users/{userId}
  - name, email, plan, privacyPolicyVersion, termsAcceptedAt, createdAt, updatedAt

/pairs/{pairId}
  - userA: userId
  - userB: userId
  - pairCode: string
  - createdAt

/tasks/{taskId}
  - name, category, physicalScore, mentalScore, frequency
  - isActive: bool

/assignments/{assignmentId}
  - pairId (composite index)
  - taskId
  - assigneeId
  - dueDate (Timestamp)
  - completed: bool
  - completedAt: Timestamp
  - note: string

/gratitudes/{gratitudeId}
  - fromId, toId
  - assignmentId (optional)
  - message (optional)
  - createdAt
```

### 3.2 主なクエリ

```sql
-- 今週のペアのタスク一覧
assignments.where("pairId", "==", pairId)
           .where("dueDate", ">=", startOfWeek)
           .where("dueDate", "<=", endOfWeek)

-- 個人の未完了タスク
assignments.where("assigneeId", "==", userId)
           .where("completed", "==", false)

-- 今月の感謝ポイント集計
gratitudes.where("toId", "==", userId)
          .where("createdAt", ">=", startOfMonth)
```

---

## 4. バリデーションルール

### 4.1 タスク関連

| 項目 | ルール |
|---|---|
| physical_score | 1〜10の整数 |
| mental_score | 1〜10の整数 |
| カテゴリ | 固定リスト（料理/掃除/買い物/育児/ペット/手続き/その他）のみ |
| 頻度 | daily / weekly / monthly / irregular のみ |
| 担当者 | ペア内のいずれかのユーザーであること |
| due_date | 過去日付不可（当日以降） |

### 4.2 ペア関連

| 項目 | ルール |
|---|---|
| pair_code | 6文字英数字（大文字） |
| ペア参加 | pair_codeが有効かつ未使用であること |
| ペア人数 | 2名まで |

---

## 5. 負担スコア集計ロジック

### 5.1 週間集計（SQL相当）

```
SELECT
  assignee_id,
  SUM(t.physical_score) AS total_physical,
  SUM(t.mental_score) AS total_mental
FROM task_assignments a
JOIN tasks t ON a.task_id = t.id
WHERE a.pair_id = :pair_id
  AND a.due_date BETWEEN :start_date AND :end_date
GROUP BY assignee_id
```

### 5.2 アラート条件チェック

```
function check_balance_alert(pair_id):
  集計結果を取得
  userA_rate = userA_total / (userA_total + userB_total) * 100
  userB_rate = 100 - userA_rate

  if userA_rate > 65 or userB_rate > 65:
    偏りアラート → 定型文表示
  if userA_mental_rate > 70 or userB_mental_rate > 70:
    メンタル偏りアラート → 定型文表示
```

### 5.3 Firestore移行時の注意（複合インデックス）

Phase 2でFirestoreに移行する際、以下のクエリには事前に composite index の作成が必要になる：

- `assignments` コレクション: `pairId` + `dueDate`
- `assignments` コレクション: `assigneeId` + `completed`

これらのインデックスは Firebase Console からクエリ実行時のエラー通知に従って作成するか、`firestore.indexes.json` で事前定義しておく。
```
