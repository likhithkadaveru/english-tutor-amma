"""
Words I Learnt page — vocabulary log.
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from modules.database import get_vocabulary_list, init_db

st.set_page_config(
    page_title="Words I Learnt 📚",
    page_icon="📚",
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
    .word-card {
        background: #F3E5F5; border-left: 4px solid #AB47BC;
        border-radius: 12px; padding: 14px 18px; margin: 8px 0;
        font-size: 16px; line-height: 1.7;
    }
    .empty-state {
        background: #FFF0F5; border-radius: 14px;
        padding: 30px; text-align: center; font-size: 17px; color: #888;
    }
    .search-highlight { background: #FFF9C4; border-radius: 4px; padding: 0 2px; }
</style>
""",
    unsafe_allow_html=True,
)

init_db()
vocab = get_vocabulary_list()

st.markdown(
    """
<div style="background:linear-gradient(135deg,#F3E5F5 0%,#FFF8FF 100%);
            border-radius:18px; padding:20px 24px; margin-bottom:16px; text-align:center;">
    <h1>📚 Words I Learnt</h1>
    <p style="font-size:16px; color:#555; margin:0;">
        All the words you have learnt so far. Well done! ⭐
    </p>
</div>
""",
    unsafe_allow_html=True,
)

if not vocab:
    st.markdown(
        """<div class="empty-state">
        🌸 No words saved yet.<br>
        Complete a practice task and new words will appear here!
        </div>""",
        unsafe_allow_html=True,
    )
    st.stop()

total = len(vocab)
st.markdown(
    f"""<div style="text-align:center; margin-bottom:12px;">
    <span style="background:#FCE4EC; border-radius:20px; padding:8px 20px;
    font-size:16px; font-weight:700; color:#AD1457;">
    ⭐ You know {total} word{"s" if total != 1 else ""}!
    </span>
    </div>""",
    unsafe_allow_html=True,
)

# ── Search ────────────────────────────────────────────────────────────────────
search = st.text_input(
    "🔍 Search a word",
    placeholder="Type to search…",
    label_visibility="collapsed",
)

filtered = vocab
if search.strip():
    q = search.strip().lower()
    filtered = [
        w for w in vocab
        if q in w.get("word", "").lower()
        or q in w.get("meaning", "").lower()
        or q in w.get("telugu_meaning", "").lower()
    ]

if not filtered:
    st.info("No words match your search. Try a different word.")
    st.stop()

# ── Group by month ────────────────────────────────────────────────────────────
from collections import defaultdict

grouped: dict = defaultdict(list)
for w in filtered:
    dl = w.get("date_learnt", "")
    month = dl[:7] if dl else "Unknown"
    grouped[month].append(w)

for month in sorted(grouped.keys(), reverse=True):
    words_in_month = grouped[month]
    label = month if month != "Unknown" else "Earlier"
    st.markdown(f"#### 📅 {label} &nbsp; <small style='color:#bbb;'>({len(words_in_month)} words)</small>", unsafe_allow_html=True)
    for w in words_in_month:
        meaning = w.get("meaning", "")
        example = w.get("example_sentence", "")
        telugu = w.get("telugu_meaning", "")
        date_str = w.get("date_learnt", "")

        st.markdown(
            f"""<div class="word-card">
            <b style="font-size:18px;">⭐ {w.get("word","")}</b>
            &nbsp;<small style="color:#aaa;">{date_str}</small><br>
            {meaning}<br>
            {"<i style='color:#555;'>Example: " + example + "</i><br>" if example else ""}
            {"<small style='color:#7B1FA2;'>Telugu: " + telugu + "</small>" if telugu else ""}
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("---")
if st.button("🏠 Back to Home"):
    st.switch_page("app.py")
