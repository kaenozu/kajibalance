# src/kajibalance/app.py
# Streamlitメインアプリ — UI改善版
# タスク行のコンパクト化、バランス表示の改善、空状態の充実、統一カラーパレット

import streamlit as st
import pandas as pd
import altair as alt
import uuid
import random
import string
from datetime import date
from .data import (
    get_initial_tasks, load_tasks, save_tasks,
    load_assignments, save_assignments, create_assignment,
    load_gratitudes, save_gratitudes,
    load_pair, save_pair, get_next_id,
)
from .models import Task, GratitudePoint

st.set_page_config(page_title="KajiBalance", page_icon="\U0001f3e0", layout="wide")

# ── 統一カラーパレット ──
CAT_COLORS = {
    "\u6599\u7406": "#FF9F43", "\u6383\u9664": "#5B8DEF", "\u8cb7\u3044\u7269": "#2ED573",
    "\u80b2\u5150": "#FF6B6B", "\u30da\u30c3\u30c8": "#A29BFE", "\u624b\u7d9a\u304d": "#FDCB6E", "\u305d\u306e\u4ed6": "#636E72",
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
    aas = st.session_state.assignments
    tm = {t.id: t for t in load_tasks() or get_initial_tasks()}
    s = {"me": {"phys": 0, "ment": 0}, "partner": {"phys": 0, "ment": 0}}
    for a in aas:
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


def _bar(pct, color):
    """Generate an HTML balance bar with percentage inside."""
    show_pct = pct if pct > 18 else 0
    return f"""
    <div class="bar-container">
      <div class="bar-fill" style="width:{pct}%;background:{color};">
        {"<span class='bar-pct-inside'>" + str(pct) + "%</span>" if show_pct else ""}
      </div>
    </div>
    """


def page_home():
    s = calc_scores()
    pair = st.session_state.pair
    aas = st.session_state.assignments
    today_aas = [a for a in aas if a.due_date == date.today()]

    st.markdown(CSS, unsafe_allow_html=True)
    st.title("\U0001f4ca \u4eca\u9031\u306e\u30d0\u30e9\u30f3\u30b9")

    col_left, col_right = st.columns([7, 5])

    with col_left:
        with st.container(border=True):
            st.markdown("**\u8ca0\u62c5\u6bd4\u7387**")
            items = [
                (f"\U0001f464 {pair.my_name} \u00b7 \u7269\u7406", s["me_phys"], BLUE),
                (f"\U0001f464 {pair.partner_name} \u00b7 \u7269\u7406", s["partner_phys"], "#9AC4FF"),
                (f"\U0001f9e0 {pair.my_name} \u00b7 \u30e1\u30f3\u30bf\u30eb", s["me_ment"], ORANGE),
                (f"\U0001f9e0 {pair.partner_name} \u00b7 \u30e1\u30f3\u30bf\u30eb", s["partner_ment"], "#FFB878"),
            ]
            for label, pct, color in items:
                c1, c2, c3 = st.columns([2.2, 6, 0.8])
                c1.caption(label)
                c2.markdown(_bar(pct, color), unsafe_allow_html=True)
                c3.markdown(f"<span style='font-size:1.1rem;font-weight:800;color:{color};'>{pct}%</span>", unsafe_allow_html=True)

        if s["me_ment"] > 65 or s["me_phys"] > 65:
            msgs = []
            if s["me_ment"] > 65:
                msgs.append(
                    f"\U0001f9e0 <b>\u30e1\u30f3\u30bf\u30eb\u8ca0\u62c5\u304c\u504f\u3063\u3066\u3044\u307e\u3059</b> \u2014 "
                    f"{pair.my_name}\u3055\u3093\u306e\u982d\u3092\u4f7f\u3046\u5bb6\u4e8b\u304c{s['me_ment']}%\u3002"
                    f"\u6765\u9031\u306f\u5206\u62c5\u3092\u898b\u76f4\u3057\u307e\u3057\u3087\u3046"
                )
            if s["me_phys"] > 65:
                msgs.append(
                    f"\U0001f4aa <b>\u7269\u7406\u8ca0\u62c5\u304c\u504f\u3063\u3066\u3044\u307e\u3059</b> \u2014 "
                    f"{pair.my_name}\u3055\u3093\u306e\u4f53\u3092\u4f7f\u3046\u5bb6\u4e8b\u304c{s['me_phys']}%"
                )
            for m in msgs:
                st.markdown(f"<div class='alert-custom warning'>{m}</div>", unsafe_allow_html=True)

    with col_right:
        with st.container(border=True):
            st.markdown("**\u4eca\u65e5\u306e\u30bf\u30b9\u30af**")
            if not today_aas:
                st.markdown("<div class='empty-state'><span class='emoji'>\U0001f389</span>\u4eca\u65e5\u306e\u30bf\u30b9\u30af\u306f\u3042\u308a\u307e\u305b\u3093</div>", unsafe_allow_html=True)
            else:
                tasks = load_tasks() or get_initial_tasks()
                tm = {t.id: t for t in tasks}
                for a in today_aas:
                    t = tm.get(a.task_id)
                    if not t:
                        continue
                    assignee = pair.my_name if a.assignee_id == "me" else pair.partner_name
                    c1, c2, c3 = st.columns([0.4, 4, 1.6])
                    done = c1.checkbox("", value=a.completed, key=f"ht_{a.id}", label_visibility="collapsed")
                    if done != a.completed:
                        a.completed = done
                        persist()
                    c2.markdown(f"**{t.name}**")
                    cat_color = CAT_COLORS.get(t.category, "#999")
                    c3.markdown(f"<span class='tag' style='background:{cat_color}20;color:{cat_color};'>{assignee}</span>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**\u611f\u8b1d\u30dd\u30a4\u30f3\u30c8**")
        grats = st.session_state.gratitudes
        from_me = sum(1 for g in grats if g.from_id == "me")
        to_me = sum(1 for g in grats if g.to_id == "me")
        c1, c2, c3 = st.columns([1, 1, 3])
        c1.metric(f"{pair.my_name}\u2192{pair.partner_name}", from_me)
        c2.metric(f"{pair.partner_name}\u2192{pair.my_name}", to_me)


def page_tasks():
    tasks = load_tasks() or get_initial_tasks()
    aas = st.session_state.assignments
    pair = st.session_state.pair

    st.markdown(CSS, unsafe_allow_html=True)
    st.title("\U0001f4cb \u30bf\u30b9\u30af\u7ba1\u7406")

    col_filter, col_add = st.columns([3, 2])
    with col_filter:
        cats = ["\u3059\u3079\u3066"] + list(dict.fromkeys(t.category for t in tasks))
        sel_cat = st.selectbox("\u30ab\u30c6\u30b4\u30ea\u30d5\u30a3\u30eb\u30bf\u30fc", cats, label_visibility="collapsed")
    with col_add:
        expand = st.popover("\uff0b \u30bf\u30b9\u30af\u8ffd\u52a0", use_container_width=True)
        with expand:
            nn = st.text_input("\u30bf\u30b9\u30af\u540d", placeholder="\u30bf\u30b9\u30af\u540d", label_visibility="collapsed")
            nc = st.selectbox("\u30ab\u30c6\u30b4\u30ea", ["\u6599\u7406", "\u6383\u9664", "\u8cb7\u3044\u7269", "\u80b2\u5150", "\u30da\u30c3\u30c8", "\u624b\u7d9a\u304d", "\u305d\u306e\u4ed6"], label_visibility="collapsed")
            if st.button("\u8ffd\u52a0", use_container_width=True) and nn:
                tid = get_next_id(tasks)
                tasks.append(Task(id=tid, name=nn, category=nc, physical_score=5, mental_score=3, default_frequency="irregular"))
                save_tasks(tasks)
                st.rerun()

    filtered = tasks if sel_cat == "\u3059\u3079\u3066" else [t for t in tasks if t.category == sel_cat]

    for t in filtered:
        existing = next((a for a in aas if a.task_id == t.id), None)
        cat_color = CAT_COLORS.get(t.category, "#999")
        assigned = existing is not None
        assignee = existing.assignee_id if existing else None

        with st.container(border=True):
            cols = st.columns([0.35, 4.5, 1.5, 0.65])
            done = cols[0].checkbox("", value=existing.completed if existing else False, key=f"c_{t.id}", label_visibility="collapsed", disabled=not assigned)
            if existing and done != existing.completed:
                existing.completed = done
                persist()

            badges = (
                f"<span class='badge'>\U0001f4aa{t.physical_score}</span>"
                f"<span class='badge'>\U0001f9e0{t.mental_score}</span>"
            )
            cols[1].markdown(
                f"**{t.name}** "
                f"<span class='tag' style='background:{cat_color}20;color:{cat_color};'>\u25cf {t.category}</span> "
                f"{badges}",
                unsafe_allow_html=True,
            )

            opts = ["\u672a\u5272\u5f53", pair.my_name, pair.partner_name]
            def_idx = 0
            if assignee == "me":
                def_idx = 1
            elif assignee == "partner":
                def_idx = 2
            selected = cols[2].selectbox("\u62c5\u5f53", opts, index=def_idx, key=f"a_{t.id}", label_visibility="collapsed")

            if selected == pair.my_name:
                new_aid = "me"
            elif selected == pair.partner_name:
                new_aid = "partner"
            else:
                new_aid = None

            if new_aid and not existing:
                st.session_state.assignments.append(create_assignment(t.id, new_aid))
                persist()
                st.rerun()
            elif new_aid and existing and existing.assignee_id != new_aid:
                existing.assignee_id = new_aid
                persist()

            if existing and existing.completed:
                sent = existing.id in st.session_state.gratitude_sent
                if not sent:
                    if cols[3].button("\U0001f44d", key=f"thx_{t.id}", help="\u3042\u308a\u304c\u3068\u3046\u3092\u9001\u308b"):
                        st.session_state.gratitudes.append(GratitudePoint(
                            id=str(uuid.uuid4())[:8],
                            from_id="partner" if assignee == "me" else "me",
                            to_id=assignee or "me",
                            task_id=t.id,
                        ))
                        st.session_state.gratitude_sent.add(existing.id)
                        persist()
                        st.rerun()
                else:
                    cols[3].success("\U0001f44d")


def page_analysis():
    pair = st.session_state.pair
    s = calc_scores()
    aas = st.session_state.assignments
    tasks = load_tasks() or get_initial_tasks()
    tm = {t.id: t for t in tasks}

    st.markdown(CSS, unsafe_allow_html=True)
    st.title("\U0001f4ca \u8ca0\u62c5\u5206\u6790")

    tab1, tab2 = st.tabs(["\u30ab\u30c6\u30b4\u30ea\u5225", "\u7269\u7406 vs \u30e1\u30f3\u30bf\u30eb"])

    with tab1:
        cd = {}
        for a in aas:
            if a.completed:
                t = tm.get(a.task_id)
                if t:
                    cd.setdefault(t.category, {"me_phys": 0, "me_ment": 0, "partner_phys": 0, "partner_ment": 0})
                    uid = "me" if a.assignee_id == "me" else "partner"
                    cd[t.category][f"{uid}_phys"] += t.physical_score
                    cd[t.category][f"{uid}_ment"] += t.mental_score

        if cd:
            df = pd.DataFrame([
                {"\u30ab\u30c6\u30b4\u30ea": cat, f"{pair.my_name}": v["me_phys"] + v["me_ment"],
                 f"{pair.partner_name}": v["partner_phys"] + v["partner_ment"]}
                for cat, v in cd.items()
            ])
            melted = df.melt(id_vars=["\u30ab\u30c6\u30b4\u30ea"], var_name="\u62c5\u5f53\u8005", value_name="\u8ca0\u62c5")
            chart = alt.Chart(melted).mark_bar(opacity=0.85, cornerRadius=4).encode(
                x=alt.X("\u30ab\u30c6\u30b4\u30ea:N", sort="-y"),
                y="\u8ca0\u62c5:Q",
                color=alt.Color("\u62c5\u5f53\u8005:N", scale=alt.Scale(range=[BLUE, ORANGE])),
                column=alt.Column("\u62c5\u5f53\u8005:N"),
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.markdown("<div class='empty-state'><span class='emoji'>\U0001f4ed</span>\u5b8c\u4e86\u3057\u305f\u30bf\u30b9\u30af\u304c\u3042\u308a\u307e\u305b\u3093<br>\u30bf\u30b9\u30af\u3092\u5b8c\u4e86\u3059\u308b\u3068\u30b0\u30e9\u30d5\u304c\u8868\u793a\u3055\u308c\u307e\u3059</div>", unsafe_allow_html=True)

        with st.expander("\u30ab\u30c6\u30b4\u30ea\u5225 \u8ca0\u62c5\u30b9\u30b3\u30a2\u8a73\u7d30"):
            if cd:
                detail = pd.DataFrame([
                    {"\u30ab\u30c6\u30b4\u30ea": cat,
                     f"{pair.my_name} \u7269\u7406": v["me_phys"],
                     f"{pair.my_name} \u30e1\u30f3\u30bf\u30eb": v["me_ment"],
                     f"{pair.partner_name} \u7269\u7406": v["partner_phys"],
                     f"{pair.partner_name} \u30e1\u30f3\u30bf\u30eb": v["partner_ment"]}
                    for cat, v in cd.items()
                ])
                st.dataframe(detail, hide_index=True, use_container_width=True)

    with tab2:
        ratio_df = pd.DataFrame({
            "\u7a2e\u985e": ["\u7269\u7406\u8ca0\u62c5", "\u30e1\u30f3\u30bf\u30eb\u8ca0\u62c5"],
            pair.my_name: [s["me_phys"], s["me_ment"]],
            pair.partner_name: [s["partner_phys"], s["partner_ment"]],
        })
        ratio = alt.Chart(ratio_df).transform_fold(
            [pair.my_name, pair.partner_name], as_=["\u62c5\u5f53\u8005", "\u5024"]
        ).mark_bar(opacity=0.85, cornerRadius=4).encode(
            x=alt.X("\u7a2e\u985e:N"),
            y="\u5024:Q",
            color=alt.Color("\u62c5\u5f53\u8005:N", scale=alt.Scale(range=[BLUE, ORANGE])),
            xOffset="\u62c5\u5f53\u8005:N",
        ).properties(height=300)
        st.altair_chart(ratio, use_container_width=True)

        with st.container(border=True):
            st.markdown("**\u30b5\u30de\u30ea\u30fc**")
            cols = st.columns(4)
            cols[0].metric(f"{pair.my_name} \u7269\u7406", f"{s['me_phys']}%")
            cols[1].metric(f"{pair.my_name} \u30e1\u30f3\u30bf\u30eb", f"{s['me_ment']}%")
            cols[2].metric(f"{pair.partner_name} \u7269\u7406", f"{s['partner_phys']}%")
            cols[3].metric(f"{pair.partner_name} \u30e1\u30f3\u30bf\u30eb", f"{s['partner_ment']}%")


def page_settings():
    pair = st.session_state.pair
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("\u2699\ufe0f \u8a2d\u5b9a")

    with st.container(border=True):
        st.markdown("**\U0001f464 \u30d7\u30ed\u30d5\u30a3\u30fc\u30eb**")
        my_name = st.text_input("\u3042\u306a\u305f\u306e\u540d\u524d", value=pair.my_name)
        partner_name = st.text_input("\u30d1\u30fc\u30c8\u30ca\u30fc\u306e\u540d\u524d", value=pair.partner_name)
        if my_name != pair.my_name or partner_name != pair.partner_name:
            pair.my_name = my_name
            pair.partner_name = partner_name
            persist()

    with st.container(border=True):
        st.markdown("**\U0001f517 \u30da\u30a2\u9023\u643a**")
        if not pair.invite_code:
            pair.invite_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            persist()
        c1, c2 = st.columns([3, 1])
        c1.code(pair.invite_code)
        if c2.button("\u518d\u751f\u6210", use_container_width=True):
            pair.invite_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            persist()
            st.rerun()
        status = "\u2705 \u63a5\u7d9a\u6e08\u307f" if pair.paired else "\u23f3 \u672a\u63a5\u7d9a"
        st.markdown(f"\u30b9\u30c6\u30fc\u30bf\u30b9: {status}")
        invite = st.text_input("\u76f8\u624b\u306e\u30b3\u30fc\u30c9\u3092\u5165\u529b", placeholder="XXXXXX")
        if st.button("\u63a5\u7d9a", use_container_width=True) and invite:
            if invite.strip().upper() == pair.invite_code:
                pair.paired = True
                persist()
                st.success("\u30da\u30a2\u63a5\u7d9a\u5b8c\u4e86\uff01")
                st.rerun()
            else:
                st.error("\u30b3\u30fc\u30c9\u304c\u4e00\u81f4\u3057\u307e\u305b\u3093")

    with st.container(border=True):
        st.markdown("**\U0001f514 \u901a\u77e5**")
        st.toggle("\u671d\u306e\u30ea\u30de\u30a4\u30f3\u30c0\u30fc (07:00)", value=True)
        st.toggle("\u30bf\u30b9\u30af\u5b8c\u4e86\u901a\u77e5", value=True)
        st.toggle("\u30d0\u30e9\u30f3\u30b9\u30a2\u30e9\u30fc\u30c8", value=True)

    with st.container(border=True):
        st.markdown("**\u2b50 \u30d7\u30ec\u30df\u30a2\u30e0**")
        st.info("\u73fe\u5728: \u7121\u6599\u30d7\u30e9\u30f3")
        st.button("\u30a2\u30c3\u30d7\u30b0\u30ec\u30fc\u30c9", type="primary", use_container_width=True, disabled=True)
        st.caption("\u30d7\u30ec\u30df\u30a2\u30e0: \u30bf\u30b9\u30af\u7121\u5236\u9650\u30fb\u6708\u9593\u30b0\u30e9\u30d5\u30fb\u8a73\u7d30\u5206\u6790\uff08\u6e96\u5099\u4e2d\uff09")

    with st.container(border=True):
        st.markdown("**\U0001f4ca \u30c7\u30fc\u30bf\u7ba1\u7406**")
        if st.button("\u30c7\u30fc\u30bf\u3092\u30ea\u30bb\u30c3\u30c8", use_container_width=True):
            for k in ["assignments", "gratitudes", "pair", "gratitude_sent"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


def main():
    init_state()
    persist()

    with st.sidebar:
        st.title("\U0001f3e0 KajiBalance")
        st.caption("\u898b\u3048\u306a\u3044\u5bb6\u4e8b\u3092\u53ef\u8996\u5316\u3059\u308b")
        st.divider()

        page = st.radio(
            "\u30ca\u30d3\u30b2\u30fc\u30b7\u30e7\u30f3",
            ["\U0001f4ca \u30db\u30fc\u30e0", "\U0001f4cb \u30bf\u30b9\u30af", "\U0001f4c8 \u5206\u6790", "\u2699\ufe0f \u8a2d\u5b9a"],
            label_visibility="collapsed",
        )

        st.divider()
        grats = st.session_state.gratitudes
        to_me = sum(1 for g in grats if g.to_id == "me")
        st.metric("\U0001f44d \u3082\u3089\u3063\u305f\u611f\u8b1d", to_me)
        st.caption("\u00a9 2026 KajiBalance")

    pg = page.split(" ")[1]
    pages = {"\u30db\u30fc\u30e0": page_home, "\u30bf\u30b9\u30af": page_tasks, "\u5206\u6790": page_analysis, "\u8a2d\u5b9a": page_settings}
    pages[pg]()


if __name__ == "__main__":
    main()
