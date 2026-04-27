"""
All prompt-builder functions.
Each returns a plain string ready to send to OpenAI.
JSON structure is described in prose so braces don't need escaping.
"""

import json
from datetime import date


# ── Task generation ──────────────────────────────────────────────────────────

def build_task_generation_prompt(profile: dict, recent_sessions: list) -> str:
    recent_types = [s.get("task_type", "") for s in recent_sessions[:5] if s.get("task_type")]
    weak_areas = profile.get("common_mistakes", [])
    vocab_count = len(profile.get("vocabulary_learnt", []))

    last_session_note = ""
    if recent_sessions:
        last = recent_sessions[0]
        last_session_note = (
            f"Her last session was on {last.get('date', 'recently')} "
            f"and the topic was: {last.get('task_type', 'general practice')}."
        )

    task_types = (
        "write_sentences, describe_food, shopping_conversation, doctor_visit, "
        "family_conversation, read_and_answer, learn_words, past_tense, "
        "present_tense, question_answer, diary_writing"
    )

    return f"""You are a warm, encouraging English tutor for a Telugu-speaking woman named Amma.
She completed a basic 2-month English class and is a beginner learner.
Your tone should always be gentle, patient, and confidence-building.

Learner profile:
- Level: {profile.get("current_level", "beginner")}
- Telugu support preference: {profile.get("telugu_support_level", "medium")}
- Common mistakes so far: {", ".join(weak_areas) if weak_areas else "still discovering"}
- Vocabulary words learnt so far: {vocab_count}
- Recent topics (avoid repeating last 2-3): {", ".join(recent_types) if recent_types else "none yet"}
- {last_session_note}
- Today's date: {date.today().strftime("%A, %B %d, %Y")}

Choose ONE task type from: {task_types}

Pick a task that:
1. Avoids repeating the last 2 topics if possible
2. Gently addresses a weak area if one exists
3. Is achievable in 5-10 minutes for a beginner
4. Relates to everyday Telugu household life (cooking, family, market, health)

Return valid JSON with exactly these fields:
- task_type: one of the task type strings above
- task_title: short friendly title (e.g. "Writing about your day")
- task_instruction: clear warm English instruction (2-3 sentences max)
- telugu_instruction: Telugu translation of the instruction
- example_answer: a simple complete example answer she can look at
- easier_version_instruction: a simpler version if she gets stuck
- easier_telugu_instruction: Telugu for the easier version
- grammar_focus: the grammar concept this task practises (e.g. "past tense verbs")
- encouragement_opening: a warm 2-sentence greeting referencing what she did recently if known
"""


# ── Answer analysis ──────────────────────────────────────────────────────────

def build_feedback_prompt(task: str, task_type: str, user_answer: str, profile: dict) -> str:
    return f"""You are a warm, patient English tutor analysing the answer of a Telugu-speaking beginner named Amma.

Her Telugu support preference: {profile.get("telugu_support_level", "medium")}
Her common mistakes so far: {", ".join(profile.get("common_mistakes", [])) or "none recorded yet"}

Task she was given ({task_type}):
{task}

Her answer:
{user_answer}

Rules for your feedback:
1. ALWAYS begin with genuine praise for her effort — she deserves encouragement
2. Give MAXIMUM 3 corrections — do not overwhelm her
3. NEVER use: wrong, incorrect, bad grammar, failed, mistake (say "small correction", "almost right", "let's improve", "nice try")
4. If the answer is blank or just 1-2 words, gently encourage her to try more
5. Telugu explanations only for grammar points that are confusing for Telugu speakers
6. Keep the whole feedback SHORT and WARM
7. Suggest 1-2 new vocabulary words relevant to her answer

Return valid JSON with exactly these fields:
- encouragement: warm praise for her effort (1-2 sentences, always positive)
- understood_meaning: true or false — did you understand what she was trying to say?
- corrected_version: the full corrected/improved version of her answer (gentle rewrite, not harsh)
- small_corrections: array of up to 3 objects, each with: original, correction, explanation, telugu_hint
- new_words: array of up to 2 objects, each with: word, meaning, example_sentence, telugu_meaning
- grammar_focus: the main grammar topic touched by her answer (e.g. "past tense")
- weak_area_detected: one short phrase if a recurring issue is noticed, else empty string
- confidence_note: one of "beginner", "building", "growing", "confident"
- next_task_suggestion: one short encouraging suggestion for what to practise next
- telugu_closing: optional short warm closing message in Telugu (leave empty string if not needed)
"""


# ── Easier task ───────────────────────────────────────────────────────────────

def build_easier_task_prompt(original_task: str, task_type: str) -> str:
    return f"""You are a warm English tutor. The learner found this task too difficult:

Original task: {original_task}
Task type: {task_type}

Create a simpler version that:
1. Keeps the same general topic
2. Requires only 1-2 very short sentences
3. Gives clear sentence starters so she just fills in the blank
4. Feels achievable and not scary

Return valid JSON with exactly these fields:
- task_instruction: simpler English instruction (1-2 sentences)
- telugu_instruction: Telugu translation
- example_answer: very simple completed example
- sentence_starters: array of 3 sentence starters she can complete (e.g. "Today I cooked ___.")
"""


# ── Extra practice ────────────────────────────────────────────────────────────

def build_extra_practice_prompt(profile: dict, session_type: str = "general") -> str:
    weak = ", ".join(profile.get("common_mistakes", [])) or "none yet"
    recent_vocab = profile.get("vocabulary_learnt", [])[-5:]

    return f"""You are a warm English tutor creating a bonus practice activity for Amma.

Her profile:
- Level: {profile.get("current_level", "beginner")}
- Common mistakes: {weak}
- Recent vocabulary: {", ".join(recent_vocab) if recent_vocab else "none yet"}
- Requested session type: {session_type}

Create ONE fun extra practice activity. Make it different and engaging.
Connect it to everyday Telugu household life if possible.

Return valid JSON with exactly these fields:
- task_type: the practice type (e.g. "shopping_conversation")
- task_title: short friendly title
- task_instruction: clear warm English instruction
- telugu_instruction: Telugu translation
- example_answer: simple complete example
- fun_fact: one interesting English tip or useful phrase for daily life
- grammar_focus: the grammar concept this practises
"""


# ── Weekly summary (for Likhith) ──────────────────────────────────────────────

def build_weekly_summary_prompt(sessions: list, profile: dict) -> str:
    session_details = [
        {
            "date": s.get("date"),
            "task_type": s.get("task_type"),
            "weak_area": s.get("weak_area_detected"),
            "confidence": s.get("confidence_level"),
            "grammar_focus": s.get("grammar_focus"),
        }
        for s in sessions
    ]

    return f"""You are summarising a week of English learning for Likhith, who built this app for his mum Amma.

Sessions this week: {len(sessions)}
Learner profile:
- Level: {profile.get("current_level", "beginner")}
- Common mistakes detected: {", ".join(profile.get("common_mistakes", [])) or "none"}
- Total vocabulary learnt: {len(profile.get("vocabulary_learnt", []))}

Session details:
{json.dumps(session_details, indent=2)}

Write a friendly, informative summary for Likhith. Keep it warm and positive.

Return valid JSON with exactly these fields:
- overall_progress: 2-3 sentence summary of her week
- strengths: array of 2-4 things she is doing well
- areas_to_practise: array of 2-3 areas that need gentle practice (phrased positively)
- practice_with_likhith: array of 3-5 specific conversation topics or sentences Likhith can practise with her in real life
- next_week_focus: one sentence suggesting the main focus for next week
- encouraging_note: a warm 2-sentence message Likhith can read out loud to Amma
"""
