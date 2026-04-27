"""
My Progress page — encouraging, not scary analytics.
"""

import json

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from modules.database import (
    get_learner_profile,
    get_recent_sessions,
    get_streak_and_stats,
    get_vocabulary_list,
    get_weak_areas,
    init_db,
)

st.set_page_config(
    page_title="My Progress 📊",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .stApp { background-color: #FFF8F0; }
    #MainMenu, footer, header { visibility: hidden; }
    .stButton > button {
        width: 100%; padding: 13px 16px; font-size: 16px;
        font-weight: 600; border-radius: 13px; border: none; margin: 4px 0;
    }
    h1, h2, h3 { color: #AD1457; }
    .stat-card {
        background: #FFF0F5; border-radius: 16px;
        padding: 18px; text-align: center; margin: 6px 0;
    }
    .stat-number { font-size: 36px; font-weight: 800; color: #C2185B; }
    .stat-label { font-size: 14px; color: #888; margin-top: 4px; }
    .progress-section {
        background: #F1F8E9; border-left: 5px solid #66BB6A;
        border-radius: 14px; padding: 18px 22px; margin: 14px 0;
        font-size: 16px; line-height: 1.8;
    }
    .practice-section {
        background: #FFF8E1; border-left: 5px solid #FFB300;
        border-radius: 14px; padding: 18px 22px; margin: 14px 0;
        font-size: 16px; line-height: 1.8;
    }
    .session-row {
        background: #FFF; border: 1px solid #FFE0EC;
        border-radius: 10px; padding: 12px 16px; margin: 8px 0;
        font-size: 15px; line-height: 1.6;
    }
    .calendar-grid {
        display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0;
    }
    .cal-day-done {
        width: 32px; height: 32px; background: #F06292;
        border-radius: 6px; display: inline-flex; align-items: center;
        justify-content: center; color: white; font-size: 12px; font-weight: 600;
    }
    .cal-day-missed {
        width: 32px; height: 32px; background: #EEE;
        border-radius: 6px; display: inline-flex; align-items: center;
        justify-content: center; color: #bbb; font-size: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

init_db()
profile = get_learner_profile()
stats = get_streak_and_stats()
recent_sessions = get_recent_sessions(20)
weak_areas = get_weak_areas()
vocab = get_vocabulary_list()

# ── Header ────────────────────────────────────────────────────────────────────
streak = stats.get("streak", 0)
if streak >= 7:
    streak_emoji = "🔥"
    streak_note = f"Incredible — {streak} days in a row!"
elif streak >= 3:
    streak_emoji = "⭐"
    streak_note = f"Wonderful — {streak} days in a row!"
elif streak >= 1:
    streak_emoji = "😊"
    streak_note = f"{streak} day streak!"
else:
    streak_emoji = "🌸"
    streak_note = "Start your streak today!"

st.markdown(
    f"""
<div style="background:linear-gradient(135deg,#FFE0EC 0%,#FFF0F5 100%);
            border-radius:18px; padding:22px 26px; margin-bottom:16px; text-align:center;">
    <h1>📊 My Progress</h1>
    <p style="font-size:17px; color:#555; margin:0;">
        {streak_emoji} {streak_note}<br>
        Look how much you have done! 🌸
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Stat cards ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{streak}</div>
        <div class="stat-label">🔥 Day Streak</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{stats.get("total_sessions",0)}</div>
        <div class="stat-label">✅ Tasks Done</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{stats.get("vocab_count",0)}</div>
        <div class="stat-label">📚 Words Learnt</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{stats.get("week_days",0)}</div>
        <div class="stat-label">📅 Days This Week</div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Encouraging summary ───────────────────────────────────────────────────────
total = stats.get("total_sessions", 0)
week = stats.get("week_days", 0)

if total == 0:
    summary_msg = "🌸 You haven't started yet — no problem! Start today and this page will fill up with your amazing progress."
elif week >= 5:
    summary_msg = f"🌟 This week you practised <b>{week} days</b>. That is amazing consistency! Your English is growing every day."
elif week >= 3:
    summary_msg = f"😊 This week you practised <b>{week} days</b>. You are doing so well! A little bit every day makes a big difference."
elif week >= 1:
    summary_msg = f"🌸 You practised <b>{week} day(s)</b> this week. Every practice counts. Keep going — you are doing great!"
else:
    summary_msg = "🌸 Start a new week of practice today! Even 5 minutes makes you stronger."

st.markdown(
    f"""<div class="progress-section">
    {summary_msg}
    </div>""",
    unsafe_allow_html=True,
)

# ── What you are improving ────────────────────────────────────────────────────
grammar_topics: dict = {}
for s in recent_sessions:
    topic = s.get("grammar_focus", "").strip()
    if topic:
        grammar_topics[topic] = grammar_topics.get(topic, 0) + 1

recent_task_types: dict = {}
for s in recent_sessions[:10]:
    tt = s.get("task_type", "").replace("_", " ").strip()
    if tt:
        recent_task_types[tt] = recent_task_types.get(tt, 0) + 1

if grammar_topics or recent_task_types:
    improving_items = list(recent_task_types.keys())[:3]
    st.markdown("### 🌱 You are getting better at:")
    st.markdown(
        """<div class="progress-section">"""
        + "".join(f"<p>✅ {item}</p>" for item in improving_items)
        + "</div>",
        unsafe_allow_html=True,
    )

# ── Gentle practice areas ─────────────────────────────────────────────────────
if weak_areas:
    st.markdown("### 🌸 We will practise these together:")
    st.markdown(
        """<div class="practice-section">
        <p style="color:#555; font-size:15px; margin-bottom:8px;">
        Don't worry — these just need a little more practice. You are doing great!
        </p>"""
        + "".join(
            f"<p>🔧 <b>{area}</b> <small style='color:#aaa;'>({count} time{'s' if count>1 else ''})</small></p>"
            for area, count in weak_areas
        )
        + "</div>",
        unsafe_allow_html=True,
    )

# ── Recent sessions ───────────────────────────────────────────────────────────
if recent_sessions:
    st.markdown("### 📋 Recent Practice Sessions:")
    for s in recent_sessions[:8]:
        task_label = s.get("task_type", "general").replace("_", " ").title()
        date_str = s.get("date", "")
        answer_preview = (s.get("user_answer", "") or "")[:80]
        if len(s.get("user_answer", "") or "") > 80:
            answer_preview += "…"

        # Get encouragement from feedback
        encouragement = ""
        raw_fb = s.get("ai_feedback", "")
        if raw_fb:
            try:
                fb = json.loads(raw_fb)
                encouragement = fb.get("encouragement", "")[:100]
            except Exception:
                pass

        st.markdown(
            f"""<div class="session-row">
            <b>{date_str}</b> &nbsp;·&nbsp; {task_label}<br>
            <span style="color:#555; font-style:italic;">"{answer_preview}"</span>
            {"<br><small style='color:#2E7D32;'>🌸 " + encouragement + "</small>" if encouragement else ""}
            </div>""",
            unsafe_allow_html=True,
        )

# ── Vocabulary preview ────────────────────────────────────────────────────────
recent_words = vocab[:6]
if recent_words:
    st.markdown("### 📚 Recently Learnt Words:")
    cols = st.columns(2)
    for i, w in enumerate(recent_words):
        with cols[i % 2]:
            st.markdown(
                f"""<div style="background:#F3E5F5; border-radius:10px;
                padding:10px 14px; margin:5px 0; font-size:15px;">
                <b>⭐ {w.get("word","")}</b><br>
                <small>{w.get("meaning","")}</small>
                </div>""",
                unsafe_allow_html=True,
            )

    if len(vocab) > 6:
        if st.button("📚 See All My Words"):
            st.switch_page("pages/2_Words_Learnt.py")

st.markdown("---")
if st.button("🏠 Back to Home"):
    st.switch_page("app.py")
