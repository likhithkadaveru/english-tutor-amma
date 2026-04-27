"""
Home page — Today's Practice.
Run with: streamlit run app.py
"""

import json
from datetime import date

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from modules.database import (
    clear_st_cache,
    get_cached_task_for_today,
    get_learner_profile,
    get_recent_sessions,
    get_streak_and_stats,
    get_today_sessions,
    init_db,
    save_cached_task_for_today,
    save_session,
    save_vocabulary,
    update_learner_profile,
)
from modules.tutor import analyse_answer_stream, generate_daily_task, get_easier_task

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Amma's English Tutor 🌸",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .stApp { background-color: #FFF8F0; }

    /* Hide default Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* Big mobile-friendly buttons */
    .stButton > button {
        width: 100%;
        padding: 14px 18px;
        font-size: 17px;
        font-weight: 600;
        border-radius: 14px;
        border: none;
        margin: 4px 0;
        transition: transform 0.1s, box-shadow 0.1s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }

    /* Text area */
    .stTextArea textarea {
        font-size: 17px;
        border-radius: 12px;
        border: 2px solid #FFB3C6 !important;
        background: #FFFDF8;
        padding: 12px;
        line-height: 1.6;
    }

    h1 { color: #C2185B; }
    h2, h3 { color: #AD1457; }

    .greeting-box {
        background: linear-gradient(135deg, #FFE0EC 0%, #FFF0F5 100%);
        border-radius: 18px;
        padding: 22px 26px;
        margin-bottom: 18px;
        text-align: center;
    }
    .task-box {
        background: #FFF0F5;
        border-left: 5px solid #F06292;
        border-radius: 14px;
        padding: 20px 22px;
        margin: 14px 0;
        font-size: 17px;
        line-height: 1.7;
    }
    .helper-box {
        background: #FFF8E1;
        border-left: 5px solid #FFB300;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 10px 0;
        font-size: 16px;
        line-height: 1.7;
    }
    .feedback-box {
        background: #F1F8E9;
        border-left: 5px solid #66BB6A;
        border-radius: 14px;
        padding: 20px 22px;
        margin: 14px 0;
        font-size: 17px;
        line-height: 1.7;
    }
    .correction-row {
        background: #FFFDE7;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 16px;
        line-height: 1.6;
    }
    .word-card {
        background: #F3E5F5;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 7px 0;
        font-size: 16px;
        line-height: 1.6;
    }
    .stat-chip {
        display: inline-block;
        background: #FCE4EC;
        border-radius: 20px;
        padding: 6px 16px;
        margin: 4px;
        font-size: 15px;
        font-weight: 600;
        color: #AD1457;
    }

    @media (max-width: 600px) {
        .stButton > button { font-size: 15px; padding: 12px 14px; }
        h1 { font-size: 22px; }
        .task-box, .feedback-box { font-size: 15px; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
profile = get_learner_profile()
stats = get_streak_and_stats()
recent_sessions = get_recent_sessions(10)
today_sessions = get_today_sessions()

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("current_task", None),
    ("feedback", None),
    ("show_telugu", False),
    ("show_example", False),
    ("easier_task", None),
    ("easier_mode", False),
    ("session_saved", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ───────────────────────────────────────────────────────────────────
def reset_task_state():
    st.session_state.current_task = None
    st.session_state.feedback = None
    st.session_state.show_telugu = False
    st.session_state.show_example = False
    st.session_state.easier_task = None
    st.session_state.easier_mode = False
    st.session_state.session_saved = False


def load_new_task(force_new: bool = False):
    reset_task_state()
    # Use today's cached task if available and not forcing a new one
    if not force_new:
        cached = get_cached_task_for_today()
        if cached:
            st.session_state.current_task = cached
            return
    with st.spinner("Getting your task ready... 🌸"):
        try:
            task = generate_daily_task(profile, recent_sessions)
            st.session_state.current_task = task
            save_cached_task_for_today(task)
        except Exception as e:
            st.error(f"Could not load task. Please check your API key. Error: {e}")


def effective_instruction() -> str:
    if st.session_state.easier_mode and st.session_state.easier_task:
        return st.session_state.easier_task.get(
            "task_instruction",
            st.session_state.current_task.get("task_instruction", ""),
        )
    return st.session_state.current_task.get("task_instruction", "")


# ── Greeting ──────────────────────────────────────────────────────────────────
streak = stats.get("streak", 0)
if streak >= 7:
    streak_line = f"⭐ {streak} days in a row — you are amazing!"
elif streak >= 3:
    streak_line = f"⭐ {streak} days in a row — keep going!"
elif streak == 1:
    streak_line = "⭐ You practised yesterday — great start!"
else:
    streak_line = "🌸 Welcome back! Let's practise a little today."

last_topic = ""
if recent_sessions and recent_sessions[0].get("date") != str(date.today()):
    raw = recent_sessions[0].get("task_type", "").replace("_", " ")
    last_topic = f"Last time you practised <b>{raw}</b>. " if raw else ""

st.markdown(
    f"""
<div class="greeting-box">
    <h1>🌸 Hello Amma!</h1>
    <p style="font-size:17px; color:#555; margin:0;">
        {last_topic}You are learning so nicely. 😊<br>
        {streak_line}<br>
        One small task today — no pressure, just try your best!
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ── No task loaded yet ────────────────────────────────────────────────────────
if st.session_state.current_task is None:
    if st.button("🌸 Start Today's Practice", type="primary"):
        load_new_task()
        st.rerun()

    # Show completed sessions from today
    if today_sessions:
        st.markdown("---")
        st.markdown("### ✅ You already practised today! Great job.")
        for ts in today_sessions[:2]:
            st.markdown(f"**Task:** {ts.get('task_given', '')}")
            raw_fb = ts.get("ai_feedback", "")
            if raw_fb:
                try:
                    fb = json.loads(raw_fb)
                    st.markdown(
                        f"""<div class="feedback-box">
                        {fb.get("encouragement", "🌸 Well done!")}
                        </div>""",
                        unsafe_allow_html=True,
                    )
                except Exception:
                    pass
            st.markdown("---")

        if st.button("🔄 Do Another Task"):
            load_new_task(force_new=True)
            st.rerun()
    st.stop()

# ── Task display ──────────────────────────────────────────────────────────────
task = st.session_state.current_task

st.markdown(
    f"""
<div class="task-box">
    <h3>📝 {task.get("task_title", "Today's Task")}</h3>
    <p>{task.get("task_instruction", "")}</p>
    <small style="color:#999;">Grammar focus: {task.get("grammar_focus", "")}</small>
</div>
""",
    unsafe_allow_html=True,
)

# ── Helper buttons ────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    if st.button("🔤 Telugu Help"):
        st.session_state.show_telugu = not st.session_state.show_telugu
with c2:
    if st.button("💡 Show Example"):
        st.session_state.show_example = not st.session_state.show_example

if st.session_state.show_telugu:
    st.markdown(
        f"""<div class="helper-box">
        <b>Telugu Help 🔤</b><br>
        {task.get("telugu_instruction", "")}
        </div>""",
        unsafe_allow_html=True,
    )

if st.session_state.show_example:
    st.markdown(
        f"""<div class="helper-box">
        <b>💡 Example Answer:</b><br>
        <i>{task.get("example_answer", "")}</i>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Easier version ────────────────────────────────────────────────────────────
if st.button("🐢 This is too hard — Make it Easier"):
    if not st.session_state.easier_task:
        with st.spinner("Making it a little easier... 🌸"):
            try:
                easier = get_easier_task(
                    task.get("task_instruction", ""),
                    task.get("task_type", "general"),
                )
                st.session_state.easier_task = easier
                st.session_state.easier_mode = True
            except Exception as e:
                st.error(f"Could not simplify task: {e}")
    else:
        st.session_state.easier_mode = not st.session_state.easier_mode

if st.session_state.easier_mode and st.session_state.easier_task:
    easier = st.session_state.easier_task
    st.markdown(
        f"""<div class="task-box">
        <h4>🐢 Easier Version</h4>
        <p>{easier.get("task_instruction", "")}</p>
        <p style="color:#999; font-size:14px;">Telugu: {easier.get("telugu_instruction", "")}</p>
        </div>""",
        unsafe_allow_html=True,
    )
    starters = easier.get("sentence_starters", [])
    if starters:
        st.markdown("**You can start with one of these:**")
        for s in starters:
            st.markdown(f"- *{s}*")

# ── Answer input ──────────────────────────────────────────────────────────────
st.markdown("### ✏️ Write your answer here:")
user_answer = st.text_area(
    "answer",
    placeholder="Type here… don't worry about mistakes, just try! 😊",
    height=160,
    label_visibility="collapsed",
    key="answer_input",
)

# ── Submit ────────────────────────────────────────────────────────────────────
if not st.session_state.session_saved:
    if st.button("✅ Check My Answer", type="primary"):
        if not user_answer.strip():
            st.warning("🌸 Please try writing something — even one sentence is wonderful!")
        else:
            st.markdown("### 🌸 Reading your answer…")
            try:
                # Stream the response so text appears immediately
                st.write_stream(
                    analyse_answer_stream(
                        effective_instruction(),
                        task.get("task_type", "general"),
                        user_answer,
                        profile,
                    )
                )
                fb = st.session_state.get("_streamed_feedback", {})
                st.session_state.feedback = fb

                # Persist session
                session_data = {
                    "date": str(date.today()),
                    "task_type": task.get("task_type", ""),
                    "task_given": effective_instruction(),
                    "user_answer": user_answer,
                    "ai_feedback": json.dumps(fb),
                    "corrected_sentences": fb.get("corrected_version", ""),
                    "new_vocabulary": fb.get("new_words", []),
                    "grammar_focus": fb.get("grammar_focus", ""),
                    "confidence_level": fb.get("confidence_note", ""),
                    "weak_area_detected": fb.get("weak_area_detected", ""),
                }
                save_session(session_data)
                st.session_state.session_saved = True
                clear_st_cache()

                if fb.get("new_words"):
                    save_vocabulary(fb["new_words"])

                area = fb.get("weak_area_detected", "").strip()
                if area:
                    existing = profile.get("common_mistakes", [])
                    if area not in existing:
                        existing.append(area)
                    update_learner_profile({"common_mistakes": existing[-10:]})

                st.rerun()
            except Exception as e:
                st.error(f"Could not analyse answer: {e}")

# ── Feedback display ──────────────────────────────────────────────────────────
if st.session_state.feedback:
    fb = st.session_state.feedback

    st.markdown(
        f"""<div class="feedback-box">
        <h3>🌸 Feedback</h3>
        <p style="font-size:18px;"><b>{fb.get("encouragement", "🌸 Great effort today!")}</b></p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Corrected version
    corrected = fb.get("corrected_version", "").strip()
    if corrected and corrected.lower() != user_answer.strip().lower():
        st.markdown("### ✏️ Improved Version:")
        st.markdown(
            f"""<div style="background:#E8F5E9; border-radius:12px; padding:16px;
                font-size:17px; line-height:1.7; color:#2E7D32;">{corrected}</div>""",
            unsafe_allow_html=True,
        )

    # Small corrections
    corrections = fb.get("small_corrections", [])
    if corrections:
        st.markdown("### 🔧 Small Corrections:")
        for corr in corrections[:3]:
            st.markdown(
                f"""<div class="correction-row">
                <span style="color:#E53935;">"{corr.get("original","")}"</span>
                &nbsp;→&nbsp;
                <span style="color:#2E7D32; font-weight:600;">"{corr.get("correction","")}"</span><br>
                <span style="color:#555;">{corr.get("explanation","")}</span><br>
                <small style="color:#795548;">Telugu: {corr.get("telugu_hint","")}</small>
                </div>""",
                unsafe_allow_html=True,
            )

    # New words
    new_words = fb.get("new_words", [])
    if new_words:
        st.markdown("### 📚 New Words Today:")
        for w in new_words:
            st.markdown(
                f"""<div class="word-card">
                <b>⭐ {w.get("word","")}</b> — {w.get("meaning","")}<br>
                <i>Example: {w.get("example_sentence","")}</i><br>
                <small style="color:#7B1FA2;">Telugu: {w.get("telugu_meaning","")}</small>
                </div>""",
                unsafe_allow_html=True,
            )

    # Telugu closing
    tel_close = fb.get("telugu_closing", "").strip()
    if tel_close:
        st.markdown(
            f"""<div class="helper-box">🌸 {tel_close}</div>""",
            unsafe_allow_html=True,
        )

    # Next suggestion
    next_sug = fb.get("next_task_suggestion", "").strip()
    if next_sug:
        st.markdown(f"**Next time:** {next_sug}")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🎯 Give Me One More Task!", type="primary"):
            load_new_task(force_new=True)
            st.rerun()
    with col_b:
        if st.button("📊 See My Progress"):
            st.switch_page("pages/3_My_Progress.py")
