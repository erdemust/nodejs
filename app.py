import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Turkish Proverbs Quiz",
    page_icon="🇹🇷",
    layout="centered",
)


# =====================================================
# DATABASE CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "proverbs_quiz.db"

FEEDBACK_SECONDS = 3
OPTIONS_PER_QUESTION = 4


# =====================================================
# CSS
# =====================================================

st.markdown(
    """
    <style>
    .title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: #D71920;
    }

    .subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 25px;
    }

    .proverb {
        background: #f5f5f5;
        border-left: 6px solid #D71920;
        padding: 22px;
        border-radius: 10px;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0;
        color: #222;
    }

    .correct {
        background: #d4edda;
        color: #155724;
        border: 2px solid #28a745;
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0;
        font-size: 16px;
        font-weight: 600;
    }

    .wrong {
        background: #f8d7da;
        color: #721c24;
        border: 2px solid #dc3545;
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0;
        font-size: 16px;
        font-weight: 600;
    }

    .neutral {
        background: #f7f7f7;
        color: #333;
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0;
        font-size: 16px;
    }

    .feedback {
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin: 16px 0;
    }

    .small-note {
        text-align: center;
        color: #777;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# DATABASE CONNECTION
# =====================================================

def open_connection():
    """
    Open a connection to the database beside app.py.

    Do not create a new empty database if the expected
    database file is missing.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. "
            "Place proverbs_quiz.db beside app.py."
        )

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30,
    )

    connection.row_factory = sqlite3.Row

    return connection


def get_table_columns(connection, table_name):
    """
    Return the column names for an existing SQLite table.
    """

    safe_table = table_name.replace('"', '""')

    rows = connection.execute(
        f'PRAGMA table_info("{safe_table}")'
    ).fetchall()

    return [row["name"] for row in rows]


def find_column(columns, candidates):
    """
    Find a column using case-insensitive candidate names.
    """

    lookup = {
        column.casefold(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate.casefold() in lookup:
            return lookup[candidate.casefold()]

    return None


# =====================================================
# LOAD QUESTIONS FROM SQLITE
# =====================================================

def load_questions():
    """
    Read questions from the existing database.

    Supported source-table examples:

        questions:
            proverb, answer

        proverbs:
            proverb, english

        questions:
            turkish, english_equivalent

    If a table already stores multiple-choice options,
    the loader also supports common option column names.

    The correct-answer column must contain the English
    equivalent, not the Turkish proverb.
    """

    connection = open_connection()

    try:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        # Prefer the table populated by seed_database.py.
        preferred_names = [
            "questions",
            "proverbs",
            "quiz_questions",
        ]

        table_names = [row["name"] for row in tables]

        ordered_tables = (
            [name for name in preferred_names if name in table_names]
            + [
                name for name in table_names
                if name not in preferred_names
                and name != "quiz_results"
            ]
        )

        selected_table = None
        selected_columns = None

        for table in ordered_tables:

            columns = get_table_columns(
                connection,
                table,
            )

            proverb_column = find_column(
                columns,
                [
                    "proverb",
                    "turkish_proverb",
                    "turkish",
                    "turkish_text",
                    "question",
                    "question_text",
                    "name",
                ],
            )

            answer_column = find_column(
                columns,
                [
                    "answer",
                    "correct_answer",
                    "english",
                    "english_equivalent",
                    "translation",
                    "meaning",
                    "correct_option",
                ],
            )

            if proverb_column and answer_column:
                selected_table = table
                selected_columns = columns
                break

        if selected_table is None:
            details = []

            for table in table_names:
                details.append(
                    f"{table}: "
                    f"{', '.join(get_table_columns(connection, table))}"
                )

            raise RuntimeError(
                "Could not identify the question table and its "
                "Turkish proverb / English answer columns.\n\n"
                "Tables found:\n"
                + "\n".join(details)
                + "\n\nUpdate the column candidates in load_questions()."
            )

        proverb_column = find_column(
            selected_columns,
            [
                "proverb",
                "turkish_proverb",
                "turkish",
                "turkish_text",
                "question",
                "question_text",
                "name",
            ],
        )

        answer_column = find_column(
            selected_columns,
            [
                "answer",
                "correct_answer",
                "english",
                "english_equivalent",
                "translation",
                "meaning",
                "correct_option",
            ],
        )

        # Optional pre-existing choices.
        option_columns = []

        for candidates in [
            ["option_a", "option1", "choice_a", "option_1"],
            ["option_b", "option2", "choice_b", "option_2"],
            ["option_c", "option3", "choice_c", "option_3"],
            ["option_d", "option4", "choice_d", "option_4"],
        ]:
            column = find_column(
                selected_columns,
                candidates,
            )

            if column:
                option_columns.append(column)

        safe_table = selected_table.replace('"', '""')
        safe_proverb = proverb_column.replace('"', '""')
        safe_answer = answer_column.replace('"', '""')

        sql = (
            f'SELECT "{safe_proverb}" AS proverb, '
            f'"{safe_answer}" AS answer'
        )

        for index, column in enumerate(option_columns):
            safe_column = column.replace('"', '""')
            sql += f', "{safe_column}" AS option_{index}'

        sql += f' FROM "{safe_table}"'

        rows = connection.execute(sql).fetchall()

        questions = []

        for row in rows:

            proverb = row["proverb"]
            answer = row["answer"]

            if proverb is None or answer is None:
                continue

            proverb = str(proverb).strip()
            answer = str(answer).strip()

            if not proverb or not answer:
                continue

            options = []

            for index in range(len(option_columns)):
                value = row[f"option_{index}"]

                if value is not None and str(value).strip():
                    options.append(str(value).strip())

            # Deduplicate options while preserving their order.
            options = list(dict.fromkeys(options))

            # Ensure the correct answer is always an option.
            if answer not in options:
                options.append(answer)

            questions.append({
                "proverb": proverb,
                "answer": answer,
                "options": options,
            })

        if not questions:
            raise RuntimeError(
                f"No usable questions found in table "
                f"'{selected_table}'."
            )

        # If the database stores only the proverb and correct
        # answer, generate three distractors from other answers.
        all_answers = list(dict.fromkeys(
            question["answer"]
            for question in questions
        ))

        for question in questions:

            options = question["options"]

            if len(options) < OPTIONS_PER_QUESTION:

                distractors = [
                    answer
                    for answer in all_answers
                    if answer != question["answer"]
                    and answer not in options
                ]

                needed = OPTIONS_PER_QUESTION - len(options)

                options.extend(
                    random.sample(
                        distractors,
                        min(needed, len(distractors)),
                    )
                )

            # Ensure four choices when the database contains
            # enough distinct correct answers.
            if len(options) < OPTIONS_PER_QUESTION:
                for answer in all_answers:
                    if answer not in options:
                        options.append(answer)

                    if len(options) >= OPTIONS_PER_QUESTION:
                        break

            random.shuffle(options)
            question["options"] = options

        random.shuffle(questions)

        return questions

    finally:
        connection.close()


# =====================================================
# QUIZ RESULTS TABLE
# =====================================================

def initialize_results_table():
    connection = open_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                completed_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


initialize_results_table()


# =====================================================
# SESSION STATE
# =====================================================

def reset_quiz():

    try:
        questions = load_questions()

        st.session_state.questions = questions
        st.session_state.current = 0
        st.session_state.answers = {}
        st.session_state.feedback_start = None
        st.session_state.finished = False
        st.session_state.result_saved = False
        st.session_state.load_error = None

    except Exception as error:
        st.session_state.load_error = str(error)


if "questions" not in st.session_state:
    reset_quiz()

if "player_name" not in st.session_state:
    st.session_state.player_name = "Player"


# =====================================================
# ERROR SCREEN
# =====================================================

if st.session_state.get("load_error"):

    st.error("Unable to load quiz questions from SQLite.")

    st.code(
        st.session_state.load_error
    )

    st.info(
        "Check that proverbs_quiz.db is beside app.py "
        "and that its question table contains the expected columns."
    )

    st.stop()


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("⚙️ Quiz Settings")

    st.text_input(
        "Player name",
        key="player_name",
        max_chars=50,
    )

    st.divider()

    st.write("### 📋 Rules")

    st.write("- Choose the correct English equivalent.")
    st.write("- Correct answers appear in green.")
    st.write("- Incorrect selections appear in red.")
    st.write("- Feedback lasts 3 seconds.")
    st.write("- The next question loads automatically.")

    st.caption(
        f"Database: {DB_PATH.name}"
    )

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
    '<div class="title">🇹🇷 Turkish Proverbs Quiz</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Discover Turkish wisdom, one proverb at a time!'
    '</div>',
    unsafe_allow_html=True,
)


# =====================================================
# QUESTION STATE
# =====================================================

questions = st.session_state.questions
current = st.session_state.current
total = len(questions)
answers = st.session_state.answers

score = sum(
    1
    for index, answer in answers.items()
    if answer == questions[index]["answer"]
)


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
    f"{len(answers)}/{total}",
)

st.progress(
    len(answers) / total
)

st.divider()


# =====================================================
# QUIZ SCREEN
# =====================================================

if not st.session_state.finished and current < total:

    question = questions[current]

    st.markdown(
        '<div class="proverb">'
        f'🇹🇷 {escape(question["proverb"])}'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "**Choose the correct English equivalent:**"
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
                    "Please select an answer."
                )

            else:

                st.session_state.answers[current] = selected

                st.session_state.feedback_start = time.monotonic()

                st.rerun()

    # -------------------------------------------------
    # AFTER ANSWERING
    # -------------------------------------------------

    else:

        for option in question["options"]:

            safe_option = escape(option)

            if option == question["answer"]:

                st.markdown(
                    '<div class="correct">'
                    f'✅ {safe_option}'
                    '</div>',
                    unsafe_allow_html=True,
                )

            elif option == submitted_answer:

                st.markdown(
                    '<div class="wrong">'
                    f'❌ {safe_option}'
                    '</div>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    '<div class="neutral">'
                    f'{safe_option}'
                    '</div>',
                    unsafe_allow_html=True,
                )

        if submitted_answer == question["answer"]:

            st.markdown(
                '<div class="feedback" style="color:#28a745">'
                'Correct! 🎉'
                '</div>',
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                '<div class="feedback" style="color:#dc3545">'
                'Incorrect! The correct answer is highlighted in green.'
                '</div>',
                unsafe_allow_html=True,
            )

        # -------------------------------------------------
        # AUTOMATIC ADVANCE AFTER 3 SECONDS
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

            # Native Streamlit solution: no extra packages.
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

    score = sum(
        1
        for index, answer in st.session_state.answers.items()
        if answer == st.session_state.questions[index]["answer"]
    )

    percentage = round(
        score / total * 100,
        1,
    )

    # -------------------------------------------------
    # SAVE RESULT ONCE
    # -------------------------------------------------

    if not st.session_state.result_saved:

        connection = open_connection()

        try:
            connection.execute(
                """
                INSERT INTO quiz_results (
                    player_name,
                    score,
                    total_questions,
                    percentage,
                    completed_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    st.session_state.player_name.strip() or "Player",
                    score,
                    total,
                    percentage,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            connection.commit()

            st.session_state.result_saved = True

        finally:
            connection.close()

    # -------------------------------------------------
    # RESULTS DISPLAY
    # -------------------------------------------------

    st.balloons()

    st.title("🏆 Quiz Completed!")

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

    st.divider()

    # -------------------------------------------------
    # REVIEW ANSWERS
    # -------------------------------------------------

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

    st.divider()

    # -------------------------------------------------
    # RECENT RESULTS
    # -------------------------------------------------

    st.subheader(
        "📊 Recent Quiz Results"
    )

    connection = open_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                player_name,
                score,
                total_questions,
                percentage,
                completed_at
            FROM quiz_results
            ORDER BY id DESC
            LIMIT 10
            """
        ).fetchall()

    finally:
        connection.close()

    if rows:

        df = pd.DataFrame(
            [dict(row) for row in rows]
        )

        df.columns = [
            "Player",
            "Score",
            "Total",
            "Percentage",
            "Completed At",
        ]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    if st.button(
        "🔄 Play Again",
        type="primary",
        use_container_width=True,
    ):

        reset_quiz()
        st.rerun()
