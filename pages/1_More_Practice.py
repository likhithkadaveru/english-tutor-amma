"""
More Practice page — extra tasks on demand.
"""

import json
from datetime import date

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from modules.database import (
    get_learner_profile,
    get_recent_sessions,
    init_db,
    save_session,
    save_vocabulary,
    update_learner_profile,
)
from modules.tutor import analyse_answer, get_easier_task, get_extra_practice

st.set_page_config(
    page_title="More Practice 🎯",
    page_icon="🎯",
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
    .stTextArea textarea {
        font-size: 16px; border-radius: 12px;
        border: 2px solid #FFB3C6 !important; background: #FFFDF8; padding: 12px;
    }
    h1, h2, h3 { color: #AD1457; }
    .task-box {
        background: #FFF0F5; border-left: 5px solid #F06292;
        border-radius: 14px; padding: 20px 22px; margin: 14px 0;
        font-size: 16px; line-height: 1.7;
    }
    .helper-box {
        background: #FFF8E1; border-left: 5px solid #FFB300;
        border-radius: 12px; padding: 16px 20px; margin: 10px 0;
        font-size: 15px; line-height: 1.7;
    }
    .feedback-box {
        background: #F1F8E9; border-left: 5px solid #66BB6A;
        border-radius: 14px; padding: 20px 22px; margin: 14px 0;
        font-size: 16px; line-height: 1.7;
    }
    .correction-row {
        background: #FFFDE7; border-radius: 10px;
        padding: 12px 16px; margin: 8px 0; font-size: 15px; line-height: 1.6;
    }
    .word-card {
        background: #F3E5F5; border-radius: 10px;
        padding: 12px 16px; margin: 7px 0; font-size: 15px; line-height: 1.6;
    }
</style>
""",
    unsafe_allow_html=True,
)

init_db()
profile = get_learner_profile()

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("mp_task", None),
    ("mp_feedback", None),
    ("mp_show_telugu", False),
    ("mp_show_example", False),
    ("mp_easier_task", None),
    ("mp_easier_mode", False),
    ("mp_saved", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def reset_mp():
    st.session_state.mp_task = None
    st.session_state.mp_feedback = None
    st.session_state.mp_show_telugu = False
    st.session_state.mp_show_example = False
    st.session_state.mp_easier_task = None
    st.session_state.mp_easier_mode = False
    st.session_state.mp_saved = False


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div style="background:linear-gradient(135deg,#FFE0EC 0%,#FFF0F5 100%);
            border-radius:18px; padding:20px 24px; margin-bottom:16px; text-align:center;">
    <h1>🎯 More Practice</h1>
    <p style="font-size:16px; color:#555; margin:0;">
        Choose a type of practice, or let us pick for you!
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Topic picker ──────────────────────────────────────────────────────────────
TOPIC_OPTIONS = {
    "🎲 Surprise me!": "general",
    "🍛 Food & Cooking": "describe_food",
    "🛒 Shopping": "shopping_conversation",
    "🏥 Doctor Visit": "doctor_visit",
    "👨‍👩‍👧 Family Conversation": "family_conversation",
    "📖 Read & Answer": "read_and_answer",
    "📚 Learn New Words": "learn_words",
    "⏰ Past Tense": "past_tense",
    "🕐 Present Tense": "present_tense",
    "❓ Questions & Answers": "question_answer",
    "📔 Diary Writing": "diary_writing",
}

chosen_label = st.selectbox(
    "What would you like to practise?",
    options=list(TOPIC_OPTIONS.keys()),
    index=0,
)
chosen_type = TOPIC_OPTIONS[chosen_label]

if st.button("🌸 Get This Practice Task", type="primary"):
    reset_mp()
    with st.spinner("Preparing your practice… 🌸"):
        try:
            task = get_extra_practice(profile, chosen_type)
            st.session_state.mp_task = task
        except Exception as e:
            st.error(f"Could not load task. Check your API key. Error: {e}")
    st.rerun()

if st.session_state.mp_task is None:
    st.stop()

# ── Task ──────────────────────────────────────────────────────────────────────
task = st.session_state.mp_task

st.markdown(
    f"""<div class="task-box">
    <h3>📝 {task.get("task_title", "Practice Task")}</h3>
    <p>{task.get("task_instruction", "")}</p>
    <small style="color:#999;">Grammar focus: {task.get("grammar_focus","")}</small>
    </div>""",
    unsafe_allow_html=True,
)

fun_fact = task.get("fun_fact", "").strip()
if fun_fact:
    st.markdown(
        f"""<div class="helper-box">💡 <b>Useful tip:</b> {fun_fact}</div>""",
        unsafe_allow_html=True,
    )

# ── Helper buttons ────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    if st.button("🔤 Telugu Help", key="mp_tel"):
        st.session_state.mp_show_telugu = not st.session_state.mp_show_telugu
with c2:
    if st.button("💡 Show Example", key="mp_ex"):
        st.session_state.mp_show_example = not st.session_state.mp_show_example

if st.session_state.mp_show_telugu:
    st.markdown(
        f"""<div class="helper-box">
        <b>Telugu Help 🔤</b><br>{task.get("telugu_instruction","")}
        </div>""",
        unsafe_allow_html=True,
    )

if st.session_state.mp_show_example:
    st.markdown(
        f"""<div class="helper-box">
        <b>💡 Example:</b><br><i>{task.get("example_answer","")}</i>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Easier version ────────────────────────────────────────────────────────────
if st.button("🐢 Make it Easier", key="mp_easier"):
    if not st.session_state.mp_easier_task:
        with st.spinner("Simplifying… 🌸"):
            try:
                easier = get_easier_task(
                    task.get("task_instruction", ""),
                    task.get("task_type", "general"),
                )
                st.session_state.mp_easier_task = easier
                st.session_state.mp_easier_mode = True
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.session_state.mp_easier_mode = not st.session_state.mp_easier_mode

if st.session_state.mp_easier_mode and st.session_state.mp_easier_task:
    easier = st.session_state.mp_easier_task
    st.markdown(
        f"""<div class="task-box">
        <h4>🐢 Easier Version</h4>
        <p>{easier.get("task_instruction","")}</p>
        <p style="color:#999; font-size:14px;">Telugu: {easier.get("telugu_instruction","")}</p>
        </div>""",
        unsafe_allow_html=True,
    )
    for s in easier.get("sentence_starters", []):
        st.markdown(f"- *{s}*")


def active_instruction() -> str:
    if st.session_state.mp_easier_mode and st.session_state.mp_easier_task:
        return st.session_state.mp_easier_task.get(
            "task_instruction", task.get("task_instruction", "")
        )
    return task.get("task_instruction", "")


# ── Answer input ──────────────────────────────────────────────────────────────
st.markdown("### ✏️ Write your answer here:")
user_answer = st.text_area(
    "answer",
    placeholder="Type here… just try, no pressure! 😊",
    height=150,
    label_visibility="collapsed",
    key="mp_answer",
)

# ── Submit ────────────────────────────────────────────────────────────────────
if not st.session_state.mp_saved:
    if st.button("✅ Check My Answer", type="primary", key="mp_submit"):
        if not user_answer.strip():
            st.warning("🌸 Please try writing something — even one word is a start!")
        else:
            with st.spinner("Reading your answer… 🌸"):
                try:
                    fb = analyse_answer(
                        active_instruction(),
                        task.get("task_type", "general"),
                        user_answer,
                        profile,
                    )
                    st.session_state.mp_feedback = fb

                    save_session(
                        {
                            "date": str(date.today()),
                            "task_type": task.get("task_type", ""),
                            "task_given": active_instruction(),
                            "user_answer": user_answer,
                            "ai_feedback": json.dumps(fb),
                            "corrected_sentences": fb.get("corrected_version", ""),
                            "new_vocabulary": fb.get("new_words", []),
                            "grammar_focus": fb.get("grammar_focus", ""),
                            "confidence_level": fb.get("confidence_note", ""),
                            "weak_area_detected": fb.get("weak_area_detected", ""),
                        }
                    )
                    st.session_state.mp_saved = True

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
                    st.error(f"Could not analyse: {e}")

# ── Feedback ──────────────────────────────────────────────────────────────────
if st.session_state.mp_feedback:
    fb = st.session_state.mp_feedback

    st.markdown(
        f"""<div class="feedback-box">
        <h3>🌸 Feedback</h3>
        <p style="font-size:17px;"><b>{fb.get("encouragement","🌸 Great effort!")}</b></p>
        </div>""",
        unsafe_allow_html=True,
    )

    corrected = fb.get("corrected_version", "").strip()
    if corrected and corrected.lower() != user_answer.strip().lower():
        st.markdown("### ✏️ Improved Version:")
        st.markdown(
            f"""<div style="background:#E8F5E9;border-radius:12px;padding:16px;
            font-size:16px;line-height:1.7;color:#2E7D32;">{corrected}</div>""",
            unsafe_allow_html=True,
        )

    for corr in fb.get("small_corrections", [])[:3]:
        st.markdown(
            f"""<div class="correction-row">
            <span style="color:#E53935;">"{corr.get("original","")}"</span> →
            <span style="color:#2E7D32; font-weight:600;">"{corr.get("correction","")}"</span><br>
            <span style="color:#555;">{corr.get("explanation","")}</span><br>
            <small style="color:#795548;">Telugu: {corr.get("telugu_hint","")}</small>
            </div>""",
            unsafe_allow_html=True,
        )

    for w in fb.get("new_words", []):
        st.markdown(
            f"""<div class="word-card">
            <b>⭐ {w.get("word","")}</b> — {w.get("meaning","")}<br>
            <i>Example: {w.get("example_sentence","")}</i><br>
            <small style="color:#7B1FA2;">Telugu: {w.get("telugu_meaning","")}</small>
            </div>""",
            unsafe_allow_html=True,
        )

    tel_close = fb.get("telugu_closing", "").strip()
    if tel_close:
        st.markdown(f"""<div class="helper-box">🌸 {tel_close}</div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🎯 Another Task!", type="primary", key="mp_another"):
            reset_mp()
            st.rerun()
    with col_b:
        if st.button("🏠 Home", key="mp_home"):
            st.switch_page("app.py")
