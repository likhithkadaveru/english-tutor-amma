"""
Likhith's View — password-protected parent summary page.
"""

import json
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from modules.database import (
    get_learner_profile,
    get_recent_sessions,
    get_sessions_this_week,
    get_streak_and_stats,
    get_vocabulary_list,
    get_weak_areas,
    init_db,
)
from modules.tutor import get_weekly_summary

st.set_page_config(
    page_title="Likhith's View 👀",
    page_icon="👀",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .stApp { background-color: #F8F0FF; }
    #MainMenu, footer, header { visibility: hidden; }
    .stButton > button {
        width: 100%; padding: 13px 16px; font-size: 16px;
        font-weight: 600; border-radius: 13px; border: none; margin: 4px 0;
    }
    h1, h2, h3 { color: #4A148C; }
    .summary-card {
        background: white; border-radius: 14px;
        padding: 18px 22px; margin: 10px 0;
        border: 1px solid #E1BEE7; font-size: 15px; line-height: 1.7;
    }
    .stat-card {
        background: #EDE7F6; border-radius: 14px;
        padding: 16px; text-align: center; margin: 6px 0;
    }
    .stat-number { font-size: 32px; font-weight: 800; color: #6A1B9A; }
    .stat-label { font-size: 13px; color: #888; margin-top: 4px; }
    .session-detail {
        background: #FFF; border: 1px solid #D1C4E9;
        border-radius: 10px; padding: 14px 18px; margin: 8px 0;
        font-size: 14px; line-height: 1.6;
    }
    .mistake-tag {
        display: inline-block; background: #FCE4EC;
        border-radius: 12px; padding: 4px 12px; margin: 3px;
        font-size: 13px; color: #880E4F;
    }
    .action-tag {
        display: inline-block; background: #E8F5E9;
        border-radius: 12px; padding: 4px 12px; margin: 3px;
        font-size: 13px; color: #1B5E20;
    }
</style>
""",
    unsafe_allow_html=True,
)

init_db()

# ── Password gate ─────────────────────────────────────────────────────────────
PARENT_PASSWORD = os.getenv("PARENT_PASSWORD", "")
try:
    if not PARENT_PASSWORD:
        PARENT_PASSWORD = st.secrets.get("PARENT_PASSWORD", "likhith123")
except Exception:
    PARENT_PASSWORD = "likhith123"

if "lv_authed" not in st.session_state:
    st.session_state.lv_authed = False

if not st.session_state.lv_authed:
    st.markdown(
        """
<div style="background:linear-gradient(135deg,#EDE7F6 0%,#F8F0FF 100%);
            border-radius:18px; padding:22px 26px; margin-bottom:16px; text-align:center;">
    <h1>👀 Likhith's View</h1>
    <p style="font-size:16px; color:#555;">Enter your password to see Amma's progress summary.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    pwd = st.text_input("Password", type="password", placeholder="Enter password…")
    if st.button("🔓 Enter", type="primary"):
        if pwd == PARENT_PASSWORD:
            st.session_state.lv_authed = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

# ── Authenticated view ────────────────────────────────────────────────────────
profile = get_learner_profile()
stats = get_streak_and_stats()
recent_sessions = get_recent_sessions(30)
week_sessions = get_sessions_this_week()
weak_areas = get_weak_areas()
vocab = get_vocabulary_list()

st.markdown(
    """
<div style="background:linear-gradient(135deg,#EDE7F6 0%,#F8F0FF 100%);
            border-radius:18px; padding:22px 26px; margin-bottom:16px; text-align:center;">
    <h1>👀 Likhith's View</h1>
    <p style="font-size:16px; color:#555;">Amma's learning dashboard — weekly summary & insights</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Stats ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{stats.get("streak",0)}</div>
        <div class="stat-label">🔥 Day Streak</div>
        </div>""", unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{stats.get("total_sessions",0)}</div>
        <div class="stat-label">✅ Total Sessions</div>
        </div>""", unsafe_allow_html=True
    )
with c3:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{stats.get("vocab_count",0)}</div>
        <div class="stat-label">📚 Words Learnt</div>
        </div>""", unsafe_allow_html=True
    )
with c4:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-number">{stats.get("week_days",0)}/7</div>
        <div class="stat-label">📅 This Week</div>
        </div>""", unsafe_allow_html=True
    )

# ── AI Weekly Summary ─────────────────────────────────────────────────────────
st.markdown("### 🤖 AI Weekly Summary")

if "lv_ai_summary" not in st.session_state:
    st.session_state.lv_ai_summary = None

col_gen, _ = st.columns([1, 2])
with col_gen:
    if st.button("🔄 Generate This Week's Summary", type="primary"):
        if not week_sessions:
            st.warning("No sessions this week yet. Come back after Amma has practised!")
        else:
            with st.spinner("Analysing Amma's progress… 🌸"):
                try:
                    summary = get_weekly_summary(week_sessions, profile)
                    st.session_state.lv_ai_summary = summary
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not generate summary: {e}")

if st.session_state.lv_ai_summary:
    s = st.session_state.lv_ai_summary

    st.markdown(
        f"""<div class="summary-card">
        <h4>📋 Overall Progress</h4>
        <p>{s.get("overall_progress","")}</p>
        </div>""", unsafe_allow_html=True
    )

    col_s, col_p = st.columns(2)
    with col_s:
        st.markdown("**✅ Strengths**")
        for item in s.get("strengths", []):
            st.markdown(f"- {item}")
    with col_p:
        st.markdown("**🌸 Areas to Practise**")
        for item in s.get("areas_to_practise", []):
            st.markdown(f"- {item}")

    st.markdown("**💬 Practise With Her in Real Life:**")
    for conv in s.get("practice_with_likhith", []):
        st.markdown(
            f"""<span class="action-tag">💬 {conv}</span>""",
            unsafe_allow_html=True,
        )

    focus = s.get("next_week_focus", "").strip()
    if focus:
        st.markdown(f"**📌 Next Week's Focus:** {focus}")

    enc = s.get("encouraging_note", "").strip()
    if enc:
        st.markdown(
            f"""<div style="background:#FFF8E1; border-left:4px solid #FFB300;
            border-radius:10px; padding:14px 18px; margin:12px 0; font-size:15px;">
            🌸 <b>Message to read to Amma:</b><br><i>"{enc}"</i>
            </div>""",
            unsafe_allow_html=True,
        )

# ── Repeated mistakes ─────────────────────────────────────────────────────────
if weak_areas:
    st.markdown("### 🔧 Repeated Mistakes (Areas Needing Support)")
    st.markdown("<div>", unsafe_allow_html=True)
    for area, count in weak_areas:
        st.markdown(
            f"""<span class="mistake-tag">⚠️ {area} ({count}×)</span>""",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ── Recent sessions detail ────────────────────────────────────────────────────
st.markdown("### 📋 Recent Sessions (Last 15)")
if not recent_sessions:
    st.info("No sessions yet.")
else:
    for s in recent_sessions[:15]:
        task_label = s.get("task_type", "").replace("_", " ").title()
        date_str = s.get("date", "")
        answer = s.get("user_answer", "") or ""
        corrected = s.get("corrected_sentences", "") or ""
        grammar = s.get("grammar_focus", "") or ""
        conf = s.get("confidence_level", "") or ""
        weak = s.get("weak_area_detected", "") or ""

        encouragement = ""
        raw_fb = s.get("ai_feedback", "")
        if raw_fb:
            try:
                fb = json.loads(raw_fb)
                encouragement = fb.get("encouragement", "")
            except Exception:
                pass

        with st.expander(f"📅 {date_str} — {task_label}"):
            st.markdown(f"**Her Answer:**\n> {answer}")
            if corrected and corrected != answer:
                st.markdown(f"**Corrected Version:**\n> _{corrected}_")
            if grammar:
                st.markdown(f"**Grammar focus:** {grammar}")
            if conf:
                st.markdown(f"**Confidence:** {conf}")
            if weak:
                st.markdown(
                    f"""<span class="mistake-tag">⚠️ Weak area: {weak}</span>""",
                    unsafe_allow_html=True,
                )
            if encouragement:
                st.markdown(f"*Feedback: {encouragement}*")

# ── Vocabulary learnt ─────────────────────────────────────────────────────────
if vocab:
    st.markdown(f"### 📚 All Vocabulary Learnt ({len(vocab)} words)")
    cols = st.columns(3)
    for i, w in enumerate(vocab):
        with cols[i % 3]:
            st.markdown(
                f"""<div style="background:#EDE7F6; border-radius:8px;
                padding:8px 12px; margin:4px 0; font-size:13px;">
                <b>{w.get("word","")}</b><br>
                <small style="color:#555;">{w.get("meaning","")}</small>
                </div>""",
                unsafe_allow_html=True,
            )

st.markdown("---")
col_home, col_logout = st.columns(2)
with col_home:
    if st.button("🏠 Back to Home"):
        st.switch_page("app.py")
with col_logout:
    if st.button("🔒 Log Out"):
        st.session_state.lv_authed = False
        st.rerun()
