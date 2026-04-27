"""
OpenAI API wrapper.
- generate_daily_task / get_easier_task / get_extra_practice / get_weekly_summary
  → return parsed dict (fast, small payloads)
- analyse_answer_stream
  → yields text chunks for st.write_stream, then stores full JSON in session_state
"""

import json
import os

import streamlit as st
from openai import OpenAI

from modules.prompts import (
    build_easier_task_prompt,
    build_extra_practice_prompt,
    build_feedback_prompt,
    build_task_generation_prompt,
    build_weekly_summary_prompt,
)

MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. "
            "Add OPENAI_API_KEY to your .env file (local) "
            "or Streamlit secrets (deployed)."
        )
    return OpenAI(api_key=api_key)


def _call_openai(prompt: str) -> dict:
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def generate_daily_task(profile: dict, recent_sessions: list) -> dict:
    return _call_openai(build_task_generation_prompt(profile, recent_sessions))


def analyse_answer_stream(task: str, task_type: str, user_answer: str, profile: dict):
    """
    Generator that yields text chunks for st.write_stream.
    After streaming completes, parses the full JSON and stores it
    in st.session_state['_streamed_feedback'] for the caller to read.
    """
    client = _get_client()
    prompt = build_feedback_prompt(task, task_type, user_answer, profile)

    full_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,
        stream=True,
        # No response_format here — streaming + json_object don't mix cleanly
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        full_text += delta
        yield delta

    # Parse JSON after streaming finishes
    try:
        # Extract JSON block in case the model wraps it in ```json ... ```
        text = full_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        st.session_state["_streamed_feedback"] = json.loads(text)
    except Exception:
        st.session_state["_streamed_feedback"] = {
            "encouragement": full_text,
            "small_corrections": [],
            "new_words": [],
            "corrected_version": "",
            "weak_area_detected": "",
            "grammar_focus": "",
            "confidence_note": "building",
            "next_task_suggestion": "",
            "telugu_closing": "",
        }


def get_easier_task(original_task: str, task_type: str) -> dict:
    return _call_openai(build_easier_task_prompt(original_task, task_type))


def get_extra_practice(profile: dict, session_type: str = "general") -> dict:
    return _call_openai(build_extra_practice_prompt(profile, session_type))


def get_weekly_summary(sessions: list, profile: dict) -> dict:
    return _call_openai(build_weekly_summary_prompt(sessions, profile))
