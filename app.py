import random
import sqlite3
import time
import html
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st


# =========================================================
# 1. CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Turkish Proverbs Quiz",
    page_icon="🇹🇷",
    layout="centered",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent

# Database containing Turkish proverbs and English equivalents.
DB_PATH = BASE_DIR / "proverbs_quiz.db"

# Separate database for quiz results.
RESULTS_DB_PATH = BASE_DIR / "results.db"

# External stylesheet.
CSS_PATH = BASE_DIR / "style.css"

FEEDBACK_SECONDS = 3
OPTIONS_PER_QUESTION = 4


# =========================================================
# 2. LOAD CSS
# =========================================================

def load_css():
    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            "style.css was not found. "
            "The quiz will run with Streamlit's default styling."
        )


load_css()


# =========================================================
# 3. DATABASE CONNECTIONS
# =========================================================

def get_results_connection():
    """
    Open the results database and ensure its table exists.
    """

    connection = sqlite3.connect(
        str(RESULTS_DB_PATH),
        timeout=30,
    )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_number INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            completed_at TEXT NOT NULL
        )
    """)

    connection.commit()

    return connection


def initialize_results_database():
    """
    Initialize results.db without modifying proverbs_quiz.db.
    """

    connection = get_results_connection()
    connection.close()


initialize_results_database()


# =========================================================
# 4. DETECT THE QUESTION TABLE
# =========================================================

def get_question_table(connection):
    """
    Detect a table containing Turkish proverbs and their
    English equivalents.

    Supported column-name examples:

        proverb / answer
        turkish / english
        turkish_proverb / english_equivalent
        name / meaning
    """

    tables = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    candidates = []

    proverb_candidates = [
        "proverb",
        "turkish_proverb",
        "turkish",
        "turkish_text",
        "question",
        "name",
    ]

    answer_candidates = [
        "answer",
        "english",
        "english_equivalent",
        "translation",
        "meaning",
        "correct_answer",
    ]

    for (table_name,) in tables:

        # Ignore the results table if both databases are ever
        # accidentally pointed at the same file.
        if table_name == "quiz_results":
            continue

        # Table names come from sqlite_master, not user input.
        quoted_table = '"' + table_name.replace('"', '""') + '"'

        columns = connection.execute(
            f"PRAGMA table_info({quoted_table})"
        ).fetchall()

        normalized = {
            row[1].lower().strip(): row[1]
            for row in columns
        }

        proverb_column = next(
            (
                normalized[name]
                for name in proverb_candidates
                if name in normalized
            ),
            None,
        )

        answer_column = next(
            (
                normalized[name]
                for name in answer_candidates
                if name in normalized
            ),
            None,
        )

        if proverb_column and answer_column:

            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {quoted_table}"
            ).fetchone()[0]

            candidates.append(
                (
                    row_count,
                    table_name,
                    proverb_column,
                    answer_column,
                )
            )

    if not candidates:
        raise RuntimeError(
            "Could not find a question table containing Turkish "
            "proverbs and English equivalents. Expected columns "
            "such as proverb/answer, turkish/english, "
            "or name/meaning."
        )

    # Prefer the matching table with the most records.
    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    _, table_name, proverb_column, answer_column = candidates[0]

    return table_name, proverb_column, answer_column


# =========================================================
# 5. LOAD QUESTIONS FROM proverbs_quiz.db
# =========================================================

@st.cache_data
def load_questions():

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Question database not found: {DB_PATH.name}. "
            "Place proverbs_quiz.db beside app.py."
        )

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30,
    )

    try:

        table, proverb_column, answer_column = (
            get_question_table(connection)
        )

        quoted_table = '"' + table.replace('"', '""') + '"'

        quoted_proverb = (
            '"' + proverb_column.replace('"', '""') + '"'
        )

        quoted_answer = (
            '"' + answer_column.replace('"', '""') + '"'
        )

        rows = connection.execute(
            f"""
            SELECT
                {quoted_proverb},
                {quoted_answer}
            FROM {quoted_table}
            WHERE {quoted_proverb} IS NOT NULL
              AND {quoted_answer} IS NOT NULL
              AND TRIM(CAST({quoted_proverb} AS TEXT)) != ''
              AND TRIM(CAST({quoted_answer} AS TEXT)) != ''
            """
        ).fetchall()

    finally:
        connection.close()

    unique_questions = {}
    answer_lookup = {}

    for proverb, answer in rows:

        proverb = str(proverb).strip()
        answer = str(answer).strip()

        if not proverb or not answer:
            continue

        # Remove duplicate proverb-answer pairs.
        unique_questions[(proverb, answer)] = {
            "proverb": proverb,
            "answer": answer,
        }

        # A proverb must not have conflicting correct answers.
        previous = answer_lookup.get(proverb)

        if previous is not None and previous != answer:
            raise RuntimeError(
                f"Conflicting English equivalents found for: "
                f"{proverb}"
            )

        answer_lookup[proverb] = answer

    questions = list(unique_questions.values())

    if not questions:
        raise RuntimeError(
            "No valid questions were found in proverbs_quiz.db."
        )

    if len({q["answer"] for q in questions}) < 2:
        raise RuntimeError(
            "At least two distinct English answers are required "
            "to generate multiple-choice questions."
        )

    return questions


# =========================================================
# 6. GENERATE MULTIPLE-CHOICE QUESTIONS
# =========================================================

def build_quiz_questions(source_questions):

    questions = []

    all_answers = list(
        dict.fromkeys(
            item["answer"]
            for item in source_questions
        )
    )

    for item in source_questions:

        correct_answer = item["answer"]

        distractors = [
            answer
            for answer in all_answers
            if answer != correct_answer
        ]

        number_of_distractors = min(
            OPTIONS_PER_QUESTION - 1,
            len(distractors),
        )

        options = random.sample(
            distractors,
            number_of_distractors,
        )

        options.append(correct_answer)
        random.shuffle(options)

        questions.append({
            "proverb": item["proverb"],
            "answer": correct_answer,
            "options": options,
        })

    random.shuffle(questions)

    return questions


# =========================================================
# 7. SESSION STATE AND QUIZ RESET
# =========================================================

def reset_quiz():

    source_questions = load_questions()

    st.session_state.questions = build_quiz_questions(
        source_questions
    )

    st.session_state.current = 0
    st.session_state.answers = {}
    st.session_state.feedback_start = None
    st.session_state.finished = False
    st.session_state.result_saved = False
    st.session_state.completed_at = None


if "questions" not in st.session_state:
    reset_quiz()

if "player_number" not in st.session_state:
    st.session_state.player_number = 1

if "completed_at" not in st.session_state:
    st.session_state.completed_at = None


# =========================================================
# 8. SAVE COMPLETED QUIZ
# =========================================================

def save_result(player_number, score, total, percentage):

    completed_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_results_connection()

    try:

        cursor = connection.execute("""
            INSERT INTO quiz_results (
                player_number,
                score,
                total_questions,
                percentage,
                completed_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            int(player_number),
            int(score),
            int(total),
            float(percentage),
            completed_at,
        ))

        connection.commit()

        return completed_at

    finally:
        connection.close()


# =========================================================
# 9. SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Quiz Settings")

    st.number_input(
        "Player Number",
        min_value=1,
        max_value=999999,
        step=1,
        key="player_number",
    )

    st.divider()

    st.subheader("📋 Quiz Rules")

    st.markdown("""
    - Select the correct English equivalent.
    - Correct answers appear in green.
    - Incorrect selections appear in red.
    - Feedback is shown for three seconds.
    - The next question loads automatically.
    """)

    st.caption(
        f"Questions: {DB_PATH.name}"
    )

    st.caption(
        f"Results: {RESULTS_DB_PATH.name}"
    )

    if st.button(
        "🔄 Restart Quiz",
        use_container_width=True,
    ):
        reset_quiz()
        st.rerun()


# =========================================================
# 10. HEADER
# =========================================================

st.markdown(
    """
    <div class="quiz-title">
        🇹🇷 Turkish Proverbs Quiz
    </div>
    <div class="quiz-subtitle">
        Discover Turkish wisdom, one proverb at a time!
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 11. QUIZ STATE AND SCORE
# =========================================================

questions = st.session_state.questions
current = st.session_state.current
answers = st.session_state.answers
total = len(questions)

score = sum(
    1
    for index, selected_answer in answers.items()
    if selected_answer == questions[index]["answer"]
)

answered_count = len(answers)


# =========================================================
# 12. SCOREBOARD
# =========================================================

col1, col2, col3 = st.columns(3)

col1.metric(
    "Question",
    f"{min(current + 1, total)}/{total}",
)

col2.metric(
    "Score",
    f"{score}/{total}",
)

col3.metric(
    "Answered",
    f"{answered_count}/{total}",
)

st.progress(
    min(answered_count / total, 1.0)
)

st.divider()


# =========================================================
# 13. QUESTION SCREEN
# =========================================================

if not st.session_state.finished and current < total:

    question = questions[current]

    safe_proverb = html.escape(question["proverb"])

    st.markdown(
        f"""
        <div class="proverb-card">
            🇹🇷 {safe_proverb}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "### Choose the correct English equivalent"
    )

    submitted_answer = answers.get(current)

    # -----------------------------------------------------
    # BEFORE ANSWERING
    # -----------------------------------------------------

    if submitted_answer is None:

        selected = st.radio(
            "Answer options",
            question["options"],
            key=f"choice_{current}",
            index=None,
            label_visibility="collapsed",
        )

        if st.button(
            "Check Answer",
            type="primary",
            use_container_width=True,
        ):

            if selected is None:

                st.warning(
                    "Please select an answer first."
                )

            else:

                st.session_state.answers[current] = selected

                st.session_state.feedback_start = time.time()

                st.rerun()

    # -----------------------------------------------------
    # AFTER ANSWERING
    # -----------------------------------------------------

    else:

        correct_answer = question["answer"]

        for option in question["options"]:

            safe_option = html.escape(option)

            if option == correct_answer:

                css_class = (
                    "answer-card answer-correct"
                )

                icon = "✅"

            elif option == submitted_answer:

                css_class = (
                    "answer-card answer-wrong"
                )

                icon = "❌"

            else:

                css_class = (
                    "answer-card answer-neutral"
                )

                icon = "▫️"

            st.markdown(
                f"""
                <div class="{css_class}">
                    {icon} {safe_option}
                </div>
                """,
                unsafe_allow_html=True,
            )

        if submitted_answer == correct_answer:

            st.markdown(
                """
                <div class="feedback-correct">
                    🎉 Correct! Tebrikler!
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                <div class="feedback-wrong">
                    ❌ Incorrect! The correct answer is highlighted in green.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # -------------------------------------------------
        # AUTO-ADVANCE AFTER THREE SECONDS
        # -------------------------------------------------

        if st.session_state.feedback_start is None:
            st.session_state.feedback_start = time.time()

        elapsed = (
            time.time()
            - st.session_state.feedback_start
        )

        remaining = FEEDBACK_SECONDS - elapsed

        if remaining > 0:

            st.caption(
                f"⏳ Next question in {remaining:.1f} seconds..."
            )

            time.sleep(remaining)

        if current + 1 < total:

            st.session_state.current += 1
            st.session_state.feedback_start = None

            st.rerun()

        else:

            st.session_state.finished = True
            st.session_state.completed_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            st.rerun()


# =========================================================
# 14. FINAL RESULTS
# =========================================================

if st.session_state.finished:

    questions = st.session_state.questions
    answers = st.session_state.answers
    total = len(questions)

    score = sum(
        1
        for index, selected_answer in answers.items()
        if selected_answer == questions[index]["answer"]
    )

    percentage = round(
        score / total * 100,
        1,
    )

    # -----------------------------------------------------
    # SAVE ONCE PER COMPLETED QUIZ
    # -----------------------------------------------------

    if not st.session_state.result_saved:

        completed_at = save_result(
            st.session_state.player_number,
            score,
            total,
            percentage,
        )

        st.session_state.completed_at = completed_at
        st.session_state.result_saved = True

    # -----------------------------------------------------
    # FINAL SCORE
    # -----------------------------------------------------

    st.balloons()

    st.markdown(
        "## 🏆 Quiz Completed!"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Player Number",
        st.session_state.player_number,
    )

    col2.metric(
        "Final Score",
        f"{score}/{total}",
    )

    col3.metric(
        "Percentage",
        f"{percentage}%",
    )

    st.caption(
        f"Completed at: {st.session_state.completed_at}"
    )

    if percentage == 100:

        st.success(
            "Perfect score! Mükemmel! 🇹🇷"
        )

    elif percentage >= 80:

        st.success(
            "Excellent work! Harika!"
        )

    elif percentage >= 60:

        st.info(
            "Good job! Keep learning."
        )

    elif percentage >= 40:

        st.warning(
            "Good effort! Practice makes perfect."
        )

    else:

        st.info(
            "Keep practicing. You will improve!"
        )

    # -----------------------------------------------------
    # ANSWER REVIEW
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "📖 Review Your Answers"
    )

    for index, question in enumerate(questions):

        user_answer = answers.get(index)
        correct_answer = question["answer"]

        is_correct = user_answer == correct_answer

        with st.expander(
            f"{'✅' if is_correct else '❌'} "
            f"{index + 1}. {question['proverb']}"
        ):

            if is_correct:

                st.success(
                    f"Your answer: {user_answer}"
                )

            else:

                st.error(
                    f"Your answer: {user_answer or 'Not answered'}"
                )

                st.success(
                    f"Correct answer: {correct_answer}"
                )

    # -----------------------------------------------------
    # LEADERBOARD
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "🏅 Quiz Leaderboard"
    )

    connection = get_results_connection()

    try:

        rows = connection.execute("""
            SELECT
                player_number,
                score,
                total_questions,
                percentage,
                completed_at
            FROM quiz_results
            ORDER BY
                score DESC,
                percentage DESC,
                completed_at ASC
            LIMIT 20
        """).fetchall()

    finally:

        connection.close()

    if rows:

        dataframe = pd.DataFrame(
            rows,
            columns=[
                "Player Number",
                "Score",
                "Total Questions",
                "Percentage",
                "Completed At",
            ],
        )

        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No quiz results have been recorded yet."
        )

    # -----------------------------------------------------
    # PLAY AGAIN
    # -----------------------------------------------------

    st.divider()

    if st.button(
        "🔄 Play Again",
        type="primary",
        use_container_width=True,
    ):

        reset_quiz()
        st.rerun()
