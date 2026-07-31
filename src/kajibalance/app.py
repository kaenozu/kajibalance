# src/kajibalance/app.py
# Streamlitメインアプリ — UI改善版
# タスク行のコンパクト化、バランス表示の改善、空状態の充実、統一カラーパレット

from datetime import date
import uuid

import altair as alt
import pandas as pd
import streamlit as st

from .data import (
    create_assignment,
    get_initial_tasks,
    get_next_id,
    load_assignments,
    load_gratitudes,
    load_pair,
    load_tasks,
    reset_all_data,
    save_assignments,
    save_gratitudes,
    save_pair,
    save_tasks,
)
from .models import GratitudePoint, Task

st.set_page_config(page_title="KajiBalance", page_icon="🏠", layout="wide")

CAT_COLORS = {
    "料理": "#FF9F43",
    "掃除": "#5B8DEF",
    "買い物": "#2ED573",
    "育児": "#FF6B6B",
    "ペット": "#A29BFE",
    "手続き": "#FDCB6E",
    "その他": "#636E72",
}
BLUE = "#5B8DEF"
ORANGE = "#FF9F43"
GREEN = "#2ED573"
RED = "#FF6B6B"

CSS = f"""
<style>
:root {{
    --primary: {BLUE};
    --accent: {ORANGE};
    --success: {GREEN};
    --danger: {RED};
    --bg: #F8F9FA;
    --card-bg: #FFFFFF;
    --card-border: #E9ECEF;
    --text: #212529;
    --text-muted: #868E96;
}}
.stApp {{ background: var(--bg); }}
section[data-testid="stSidebar"] {{ background: var(--card-bg); border-right: 1px solid var(--card-border); }}
.bar-container {{ background: #E9ECEF; height: 28px; border-radius: 14px; overflow: hidden; position: relative; }}
.bar-fill {{ height: 100%; border-radius: 14px; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; transition: width 0.5s ease; min-width: 2px; }}
.bar-pct-inside {{ font-size: 0.75rem; font-weight: 700; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }}
.tag {{ display: inline-block; padding: 0 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; line-height: 1.7; margin-right: 4px; }}
.badge {{ display: inline-block; padding: 0 6px; border-radius: 5px; background: #F1F3F5; font-size: 0.7rem; font-weight: 700; margin-right: 3px; }}
.empty-state {{ text-align: center; padding: 2rem 1rem; color: var(--text-muted); line-height: 1.6; }}
.empty-state .emoji {{ font-size: 2.5rem; display: block; margin-bottom: 0.5rem; }}
.alert-custom {{ padding: 0.625rem 1rem; border-radius: 10px; margin: 0.5rem 0; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; }}
.alert-custom.warning {{ background: #FFF3E0; border-left: 4px solid var(--accent); color: #E65100; }}
.alert-custom.success {{ background: #E8F5E9; border-left: 4px solid var(--success); color: #1B5E20; }}
</style>
"""


def init_state():
    st.session_state.setdefault("assignments", load_assignments())
    st.session_state.setdefault("gratitudes", load_gratitudes())
    st.session_state.setdefault("pair", load_pair())
    st.session_state.setdefault("gratitude_sent", set())
    st.session_state.setdefault("editing", None)


def persist():
    save_assignments(st.session_state.assignments)
    save_gratitudes(st.session_state.gratitudes)
    save_pair(st.session_state.pair)


def calc_scores():
    assignments = st.session_state.assignments
    task_map = {task.id: task for task in load_tasks() or get_initial_tasks()}
    scores = {"me": {"phys": 0, "ment": 0}, "partner": {"phys": 0, "ment": 0}}
    for assignment in assignments:
        if not assignment.completed:
            continue
        task = task_map.get(assignment.task_id)
        if task:
            scores[assignment.assignee_id]["phys"] += task.physical_score
            scores[assignment.assignee_id]["ment"] += task.mental_score

    total_physical = scores["me"]["phys"] + scores["partner"]["phys"] or 1
    total_mental = scores["me"]["ment"] + scores["partner"]["ment"] or 1
    return {
        "me_phys": round(scores["me"]["phys"] / total_physical * 100),
        "partner_phys": round(scores["partner"]["phys"] / total_physical * 100),
        "me_ment": round(scores["me"]["ment"] / total_mental * 100),
        "partner_ment": round(scores["partner"]["ment"] / total_mental * 100),
    }


def _bar(pct, color):
    show_pct = pct if pct > 18 else 0
    return f"""
    <div class="bar-container">
      <div class="bar-fill" style="width:{pct}%;background:{color};">
        {"<span class='bar-pct-inside'>" + str(pct) + "%</span>" if show_pct else ""}
      </div>
    </div>
    """


def page_home():
    scores = calc_scores()
    pair = st.session_state.pair
    assignments = st.session_state.assignments
    today_assignments = [assignment for assignment in assignments if assignment.due_date == date.today()]

    st.markdown(CSS, unsafe_allow_html=True)
    st.title("📊 今週のバランス")

    col_left, col_right = st.columns([7, 5])

    with col_left:
        with st.container(border=True):
            st.markdown("**負担比率**")
            items = [
                (f"👤 {pair.my_name} · 物理", scores["me_phys"], BLUE),
                (f"👤 {pair.partner_name} · 物理", scores["partner_phys"], "#9AC4FF"),
                (f"🧠 {pair.my_name} · メンタル", scores["me_ment"], ORANGE),
                (f"🧠 {pair.partner_name} · メンタル", scores["partner_ment"], "#FFB878"),
            ]
            for label, pct, color in items:
                c1, c2, c3 = st.columns([2.2, 6, 0.8])
                c1.caption(label)
                c2.markdown(_bar(pct, color), unsafe_allow_html=True)
                c3.markdown(
                    f"<span style='font-size:1.1rem;font-weight:800;color:{color};'>{pct}%</span>",
                    unsafe_allow_html=True,
                )

        if scores["me_ment"] > 65 or scores["me_phys"] > 65:
            messages = []
            if scores["me_ment"] > 65:
                messages.append(
                    f"🧠 <b>メンタル負担が偏っています</b> — "
                    f"{pair.my_name}さんの頭を使う家事が{scores['me_ment']}%。"
                    "来週は分担を見直しましょう"
                )
            if scores["me_phys"] > 65:
                messages.append(
                    f"💪 <b>物理負担が偏っています</b> — "
                    f"{pair.my_name}さんの体を使う家事が{scores['me_phys']}%"
                )
            for message in messages:
                st.markdown(
                    f"<div class='alert-custom warning'>{message}</div>",
                    unsafe_allow_html=True,
                )

    with col_right:
        with st.container(border=True):
            st.markdown("**今日のタスク**")
            if not today_assignments:
                st.markdown(
                    "<div class='empty-state'><span class='emoji'>🎉</span>今日のタスクはありません</div>",
                    unsafe_allow_html=True,
                )
            else:
                task_map = {task.id: task for task in load_tasks() or get_initial_tasks()}
                for assignment in today_assignments:
                    task = task_map.get(assignment.task_id)
                    if not task:
                        continue
                    assignee = pair.my_name if assignment.assignee_id == "me" else pair.partner_name
                    c1, c2, c3 = st.columns([0.4, 4, 1.6])
                    done = c1.checkbox(
                        "",
                        value=assignment.completed,
                        key=f"ht_{assignment.id}",
                        label_visibility="collapsed",
                    )
                    if done != assignment.completed:
                        assignment.completed = done
                        persist()
                    c2.markdown(f"**{task.name}**")
                    category_color = CAT_COLORS.get(task.category, "#999")
                    c3.markdown(
                        f"<span class='tag' style='background:{category_color}20;color:{category_color};'>{assignee}</span>",
                        unsafe_allow_html=True,
                    )

    with st.container(border=True):
        st.markdown("**感謝ポイント**")
        gratitudes = st.session_state.gratitudes
        from_me = sum(1 for gratitude in gratitudes if gratitude.from_id == "me")
        to_me = sum(1 for gratitude in gratitudes if gratitude.to_id == "me")
        c1, c2, _ = st.columns([1, 1, 3])
        c1.metric(f"{pair.my_name}→{pair.partner_name}", from_me)
        c2.metric(f"{pair.partner_name}→{pair.my_name}", to_me)


def page_tasks():
    tasks = load_tasks() or get_initial_tasks()
    assignments = st.session_state.assignments
    pair = st.session_state.pair

    st.markdown(CSS, unsafe_allow_html=True)
    st.title("📋 タスク管理")

    col_filter, col_add = st.columns([3, 2])
    with col_filter:
        categories = ["すべて"] + list(dict.fromkeys(task.category for task in tasks))
        selected_category = st.selectbox(
            "カテゴリフィルター",
            categories,
            label_visibility="collapsed",
        )
    with col_add:
        add_popover = st.popover("＋ タスク追加", use_container_width=True)
        with add_popover:
            new_name = st.text_input(
                "タスク名",
                placeholder="タスク名",
                label_visibility="collapsed",
            )
            new_category = st.selectbox(
                "カテゴリ",
                ["料理", "掃除", "買い物", "育児", "ペット", "手続き", "その他"],
                label_visibility="collapsed",
            )
            if st.button("追加", use_container_width=True) and new_name:
                task_id = get_next_id(tasks)
                tasks.append(
                    Task(
                        id=task_id,
                        name=new_name,
                        category=new_category,
                        physical_score=5,
                        mental_score=3,
                        default_frequency="irregular",
                    )
                )
                save_tasks(tasks)
                st.rerun()

    filtered = tasks if selected_category == "すべて" else [
        task for task in tasks if task.category == selected_category
    ]

    for task in filtered:
        existing = next(
            (assignment for assignment in assignments if assignment.task_id == task.id),
            None,
        )
        category_color = CAT_COLORS.get(task.category, "#999")
        assigned = existing is not None
        assignee = existing.assignee_id if existing else None

        with st.container(border=True):
            columns = st.columns([0.35, 4.5, 1.5, 0.65])
            done = columns[0].checkbox(
                "",
                value=existing.completed if existing else False,
                key=f"c_{task.id}",
                label_visibility="collapsed",
                disabled=not assigned,
            )
            if existing and done != existing.completed:
                existing.completed = done
                persist()

            badges = (
                f"<span class='badge'>💪{task.physical_score}</span>"
                f"<span class='badge'>🧠{task.mental_score}</span>"
            )
            columns[1].markdown(
                f"**{task.name}** "
                f"<span class='tag' style='background:{category_color}20;color:{category_color};'>● {task.category}</span> "
                f"{badges}",
                unsafe_allow_html=True,
            )

            options = ["未割当", pair.my_name, pair.partner_name]
            default_index = 0
            if assignee == "me":
                default_index = 1
            elif assignee == "partner":
                default_index = 2
            selected = columns[2].selectbox(
                "担当",
                options,
                index=default_index,
                key=f"a_{task.id}",
                label_visibility="collapsed",
            )

            if selected == pair.my_name:
                new_assignee = "me"
            elif selected == pair.partner_name:
                new_assignee = "partner"
            else:
                new_assignee = None

            if new_assignee and not existing:
                st.session_state.assignments.append(create_assignment(task.id, new_assignee))
                persist()
                st.rerun()
            elif new_assignee and existing and existing.assignee_id != new_assignee:
                existing.assignee_id = new_assignee
                persist()
                st.rerun()
            elif new_assignee is None and existing:
                st.session_state.assignments = [
                    assignment
                    for assignment in st.session_state.assignments
                    if assignment.id != existing.id
                ]
                st.session_state.gratitude_sent.discard(existing.id)
                persist()
                st.rerun()

            if existing and existing.completed:
                sent = existing.id in st.session_state.gratitude_sent
                if not sent:
                    if columns[3].button("👍", key=f"thx_{task.id}", help="ありがとうを送る"):
                        st.session_state.gratitudes.append(
                            GratitudePoint(
                                id=str(uuid.uuid4())[:8],
                                from_id="partner" if assignee == "me" else "me",
                                to_id=assignee or "me",
                                task_id=task.id,
                            )
                        )
                        st.session_state.gratitude_sent.add(existing.id)
                        persist()
                        st.rerun()
                else:
                    columns[3].success("👍")


def page_analysis():
    pair = st.session_state.pair
    scores = calc_scores()
    assignments = st.session_state.assignments
    task_map = {task.id: task for task in load_tasks() or get_initial_tasks()}

    st.markdown(CSS, unsafe_allow_html=True)
    st.title("📊 負担分析")

    tab_category, tab_type = st.tabs(["カテゴリ別", "物理 vs メンタル"])

    with tab_category:
        category_data = {}
        for assignment in assignments:
            if not assignment.completed:
                continue
            task = task_map.get(assignment.task_id)
            if not task:
                continue
            category_data.setdefault(
                task.category,
                {"me_phys": 0, "me_ment": 0, "partner_phys": 0, "partner_ment": 0},
            )
            user_id = "me" if assignment.assignee_id == "me" else "partner"
            category_data[task.category][f"{user_id}_phys"] += task.physical_score
            category_data[task.category][f"{user_id}_ment"] += task.mental_score

        if category_data:
            dataframe = pd.DataFrame(
                [
                    {
                        "カテゴリ": category,
                        pair.my_name: values["me_phys"] + values["me_ment"],
                        pair.partner_name: values["partner_phys"] + values["partner_ment"],
                    }
                    for category, values in category_data.items()
                ]
            )
            melted = dataframe.melt(
                id_vars=["カテゴリ"],
                var_name="担当者",
                value_name="負担",
            )
            chart = (
                alt.Chart(melted)
                .mark_bar(opacity=0.85, cornerRadius=4)
                .encode(
                    x=alt.X("カテゴリ:N", sort="-y"),
                    y="負担:Q",
                    color=alt.Color(
                        "担当者:N",
                        scale=alt.Scale(range=[BLUE, ORANGE]),
                    ),
                    column=alt.Column("担当者:N"),
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.markdown(
                "<div class='empty-state'><span class='emoji'>📭</span>完了したタスクがありません<br>タスクを完了するとグラフが表示されます</div>",
                unsafe_allow_html=True,
            )

        with st.expander("カテゴリ別 負担スコア詳細"):
            if category_data:
                detail = pd.DataFrame(
                    [
                        {
                            "カテゴリ": category,
                            f"{pair.my_name} 物理": values["me_phys"],
                            f"{pair.my_name} メンタル": values["me_ment"],
                            f"{pair.partner_name} 物理": values["partner_phys"],
                            f"{pair.partner_name} メンタル": values["partner_ment"],
                        }
                        for category, values in category_data.items()
                    ]
                )
                st.dataframe(detail, hide_index=True, use_container_width=True)

    with tab_type:
        ratio_dataframe = pd.DataFrame(
            {
                "種類": ["物理負担", "メンタル負担"],
                pair.my_name: [scores["me_phys"], scores["me_ment"]],
                pair.partner_name: [scores["partner_phys"], scores["partner_ment"]],
            }
        )
        ratio = (
            alt.Chart(ratio_dataframe)
            .transform_fold([pair.my_name, pair.partner_name], as_=["担当者", "値"])
            .mark_bar(opacity=0.85, cornerRadius=4)
            .encode(
                x=alt.X("種類:N"),
                y="値:Q",
                color=alt.Color(
                    "担当者:N",
                    scale=alt.Scale(range=[BLUE, ORANGE]),
                ),
                xOffset="担当者:N",
            )
            .properties(height=300)
        )
        st.altair_chart(ratio, use_container_width=True)

        with st.container(border=True):
            st.markdown("**サマリー**")
            columns = st.columns(4)
            columns[0].metric(f"{pair.my_name} 物理", f"{scores['me_phys']}%")
            columns[1].metric(f"{pair.my_name} メンタル", f"{scores['me_ment']}%")
            columns[2].metric(f"{pair.partner_name} 物理", f"{scores['partner_phys']}%")
            columns[3].metric(f"{pair.partner_name} メンタル", f"{scores['partner_ment']}%")


def page_settings():
    pair = st.session_state.pair
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("⚙️ 設定")

    with st.container(border=True):
        st.markdown("**👤 プロフィール**")
        my_name = st.text_input("あなたの名前", value=pair.my_name)
        partner_name = st.text_input("パートナーの名前", value=pair.partner_name)
        if my_name != pair.my_name or partner_name != pair.partner_name:
            pair.my_name = my_name
            pair.partner_name = partner_name
            persist()

    with st.container(border=True):
        st.markdown("**🔗 ペア連携**")
        st.info(
            "ペア同期は現在未実装です。この画面の記録は、このアプリを実行している端末内だけに保存されます。"
        )

    with st.container(border=True):
        st.markdown("**🔔 通知**")
        st.toggle("朝のリマインダー (07:00)", value=True, disabled=True)
        st.toggle("タスク完了通知", value=True, disabled=True)
        st.toggle("バランスアラート", value=True, disabled=True)
        st.caption("通知機能は準備中です。")

    with st.container(border=True):
        st.markdown("**⭐ プレミアム**")
        st.info("現在: 無料プラン")
        st.button(
            "アップグレード",
            type="primary",
            use_container_width=True,
            disabled=True,
        )
        st.caption("プレミアム: タスク無制限・月間グラフ・詳細分析（準備中）")

    with st.container(border=True):
        st.markdown("**📊 データ管理**")
        confirm_reset = st.checkbox(
            "保存済みのタスク、割り当て、感謝、プロフィールをすべて削除する",
            key="confirm_data_reset",
        )
        if st.button(
            "データをリセット",
            use_container_width=True,
            disabled=not confirm_reset,
        ):
            reset_all_data()
            for key in [
                "assignments",
                "gratitudes",
                "pair",
                "gratitude_sent",
                "editing",
                "confirm_data_reset",
            ]:
                st.session_state.pop(key, None)
            st.rerun()


def main():
    init_state()
    persist()

    with st.sidebar:
        st.title("🏠 KajiBalance")
        st.caption("見えない家事を可視化する")
        st.divider()

        page = st.radio(
            "ナビゲーション",
            ["📊 ホーム", "📋 タスク", "📈 分析", "⚙️ 設定"],
            label_visibility="collapsed",
        )

        st.divider()
        gratitudes = st.session_state.gratitudes
        to_me = sum(1 for gratitude in gratitudes if gratitude.to_id == "me")
        st.metric("👍 もらった感謝", to_me)
        st.caption("© 2026 KajiBalance")

    page_name = page.split(" ")[1]
    pages = {
        "ホーム": page_home,
        "タスク": page_tasks,
        "分析": page_analysis,
        "設定": page_settings,
    }
    pages[page_name]()


if __name__ == "__main__":
    main()
