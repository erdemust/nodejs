import random
import sqlite3
import time
import html

from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st


# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Turkish Proverbs Quiz",
    page_icon="🇹🇷",
    layout="centered",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "proverbs_quiz.db"
CSS_PATH = BASE_DIR / "style.css"

FEEDBACK_SECONDS = 3
OPTIONS_PER_QUESTION = 4


# =====================================================
# LOAD CSS
# =====================================================

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
            "The app will use Streamlit's default styling."
        )


load_css()


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():
    if not DB_PATH.exists():
        st.error(
            f"Database not found: {DB_PATH}\n\n"
            "Place proverbs_quiz.db in the same directory as app.py."
        )
        st.stop()

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30,
    )

    connection.execute("PRAGMA busy_timeout = 30000")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_number INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            completed_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    return connection


# =====================================================
# DETECT QUESTION TABLE AND COLUMNS
# =====================================================

def get_question_table(connection):

    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
          AND name != 'quiz_results'
        ORDER BY name
        """
    ).fetchall()

    if not tables:
        st.error(
            "No question tables were found in proverbs_quiz.db."
        )
        st.stop()

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

    candidates = []

    for (table_name,) in tables:

        columns = connection.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()

        normalized = {
            row[1].lower().strip(): row[1]
            for row in columns
        }

        proverb_column = next(
            (
                normalized[column]
                for column in proverb_candidates
                if column in normalized
            ),
            None,
        )

        answer_column = next(
            (
                normalized[column]
                for column in answer_candidates
                if column in normalized
            ),
            None,
        )

        if proverb_column and answer_column:

            row_count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
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
        st.error(
            "Could not identify the proverb and answer columns.\n\n"
            "Expected columns such as proverb/answer, "
            "turkish/english, or name/meaning."
        )

        st.write(
            "Tables found:",
            [row[0] for row in tables],
        )

        st.stop()

    # Use the compatible table containing the most rows.
    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    _, table, proverb_column, answer_column = candidates[0]

    return table, proverb_column, answer_column


# =====================================================
# LOAD QUESTIONS FROM SQLITE
# =====================================================

@st.cache_data(ttl=60)
def load_questions():

    connection = get_connection()

    try:
        table, proverb_column, answer_column = (
            get_question_table(connection)
        )

        rows = connection.execute(
            f"""
            SELECT
                "{proverb_column}",
                "{answer_column}"
            FROM "{table}"
            WHERE "{proverb_column}" IS NOT NULL
              AND "{answer_column}" IS NOT NULL
              AND TRIM("{proverb_column}") != ''
              AND TRIM("{answer_column}") != ''
            """
        ).fetchall()

    finally:
        connection.close()

    unique_questions = {}
    normalized_answers = set()

    for proverb, answer in rows:

        proverb = str(proverb).strip()
        answer = str(answer).strip()

        # Prevent duplicate proverb-answer pairs.
        key = (
            proverb.casefold(),
            answer.casefold(),
        )

        if key not in unique_questions:
            unique_questions[key] = {
                "proverb": proverb,
                "answer": answer,
            }

        normalized_answers.add(answer.casefold())

    questions = list(unique_questions.values())

    if not questions:
        st.error(
            "No questions were found in the database."
        )
        st.stop()

    if len(normalized_answers) < 2:
        st.error(
            "At least two different English answers "
            "are required to generate a quiz."
        )
        st.stop()

    return questions


# =====================================================
# GENERATE MULTIPLE-CHOICE QUESTIONS
# =====================================================

def build_quiz_questions(source_questions):

    questions = []

    all_answers = list(
        dict.fromkeys(
            question["answer"]
            for question in source_questions
        )
    )

    for item in source_questions:

        correct_answer = item["answer"]

        # Avoid duplicate answer options, ignoring case.
        distractors = [
            answer
            for answer in all_answers
            if answer.casefold() != correct_answer.casefold()
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

        questions.append(
            {
                "proverb": item["proverb"],
                "answer": correct_answer,
                "options": options,
            }
        )

    random.shuffle(questions)

    return questions


# =====================================================
# SESSION STATE
# =====================================================

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
    st.session_state.saved_player_number = None

    st.session_state.quiz_started = False


if "questions" not in st.session_state:
    reset_quiz()

if "player_number" not in st.session_state:
    st.session_state.player_number = 1


# =====================================================
# SAVE RESULTS
# =====================================================

def save_result(player_number, score, total, percentage):

    connection = get_connection()

    try:

        completed_at = datetime.now().astimezone().strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )

        connection.execute(
            """
            INSERT INTO quiz_results (
                player_number,
                score,
                total_questions,
                percentage,
                completed_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(player_number),
                int(score),
                int(total),
                float(percentage),
                completed_at,
            ),
        )

        connection.commit()

        return completed_at

    finally:
        connection.close()


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("⚙️ Quiz Settings")

    st.number_input(
        "Player Number",
        min_value=1,
        max_value=999999999,
        step=1,
        key="player_number",
        disabled=st.session_state.quiz_started,
        help="Enter your assigned competition number before starting.",
    )

    st.divider()

    st.subheader("📋 Rules")

    st.markdown(
        """
        - Choose the correct English equivalent.
        - Correct answers appear in green.
        - Incorrect selections appear in red.
        - Feedback lasts three seconds.
        - The next question loads automatically.
        - Your result and completion time are saved.
        """
    )

    st.caption(f"Database: {DB_PATH.name}")

    if st.button(
        "🔄 Restart Quiz",
        use_container_width=True,
    ):
        reset_quiz()
        st.rerun()


# =====================================================
# HEADER
# =====================================================

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


# =====================================================
# QUIZ START SCREEN
# =====================================================

if not st.session_state.quiz_started:

    st.info(
        f"🎮 Your Player Number: "
        f"{st.session_state.player_number}"
    )

    st.write(
        "Ready to test your knowledge of Turkish proverbs?"
    )

    if st.button(
        "🚀 Start Quiz",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.quiz_started = True
        st.rerun()

    st.stop()


# =====================================================
# QUIZ STATE
# =====================================================

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


# =====================================================
# SCOREBOARD
# =====================================================

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
    answered_count / total
)

st.divider()


# =====================================================
# QUESTION SCREEN
# =====================================================

if not st.session_state.finished and current < total:

    question = questions[current]

    safe_proverb = html.escape(
        question["proverb"]
    )

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

    # -------------------------------------------------
    # BEFORE ANSWERING
    # -------------------------------------------------

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

                st.session_state.feedback_start = time.monotonic()

                st.rerun()

    # -------------------------------------------------
    # AFTER ANSWERING
    # -------------------------------------------------

    else:

        correct_answer = question["answer"]

        for option in question["options"]:

            safe_option = html.escape(option)

            if option == correct_answer:

                css_class = "answer-card answer-correct"
                icon = "✅"

            elif option == submitted_answer:

                css_class = "answer-card answer-wrong"
                icon = "❌"

            else:

                css_class = "answer-card answer-neutral"
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

            st.session_state.feedback_start = time.monotonic()

        elapsed = (
            time.monotonic()
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

            st.rerun()


# =====================================================
# FINAL RESULTS
# =====================================================

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

    # -------------------------------------------------
    # SAVE ONCE
    # -------------------------------------------------

    if not st.session_state.result_saved:

        player_number = int(
            st.session_state.player_number
        )

        completed_at = save_result(
            player_number,
            score,
            total,
            percentage,
        )

        st.session_state.saved_player_number = player_number
        st.session_state.completed_at = completed_at

        st.session_state.result_saved = True

    # -------------------------------------------------
    # FINAL SCORE
    # -------------------------------------------------

    st.balloons()

    st.title("🏆 Quiz Completed!")

    st.success(
        f"🎮 Player Number: "
        f"{st.session_state.saved_player_number}"
    )

    st.caption(
        f"📅 Completed: "
        f"{st.session_state.completed_at}"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Final Score",
        f"{score}/{total}",
    )

    col2.metric(
        "Percentage",
        f"{percentage}%",
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

    # -------------------------------------------------
    # ANSWER REVIEW
    # -------------------------------------------------

    st.divider()

    st.subheader("📖 Review Your Answers")

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

    # -------------------------------------------------
    # RECENT RESULTS
    # -------------------------------------------------

    st.divider()

    st.subheader("📊 Recent Quiz Results")

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                player_number,
                score,
                total_questions,
                percentage,
                completed_at
            FROM quiz_results
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()

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
                "Date and Time",
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

    # -------------------------------------------------
    # PLAY AGAIN
    # -------------------------------------------------

    st.divider()

    if st.button(
        "🔄 Play Again",
        type="primary",
        use_container_width=True,
    ):

        reset_quiz()
        st.rerun()
