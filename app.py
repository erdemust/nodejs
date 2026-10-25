import random
import sqlite3
import time
from datetime import datetime

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
# STYLING
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
        padding: 20px;
        border-radius: 10px;
        font-size: 23px;
        font-weight: bold;
        margin: 20px 0;
    }

    .correct {
        background: #d4edda;
        color: #155724;
        border: 2px solid #28a745;
        padding: 14px;
        border-radius: 9px;
        margin: 8px 0;
    }

    .wrong {
        background: #f8d7da;
        color: #721c24;
        border: 2px solid #dc3545;
        padding: 14px;
        border-radius: 9px;
        margin: 8px 0;
    }

    .neutral {
        background: #f7f7f7;
        color: #333;
        border: 1px solid #ddd;
        padding: 14px;
        border-radius: 9px;
        margin: 8px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# SQLITE DATABASE
# =====================================================

@st.cache_resource
def get_connection():
    connection = sqlite3.connect(
        "proverbs_quiz.db",
        check_same_thread=False,
        timeout=30,
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            score INTEGER,
            total_questions INTEGER,
            percentage REAL,
            completed_at TEXT
        )
        """
    )

    connection.commit()
    return connection


con = get_connection()


# =====================================================
# QUESTION BANK: 60 QUESTIONS
# =====================================================

RAW_QUESTIONS = [
    ("Damlaya damlaya göl olur.",
     "Little by little, a little becomes a lot."),

    ("Ne ekersen onu biçersin.",
     "You reap what you sow."),

    ("Ağaç yaşken eğilir.",
     "As the twig is bent, so grows the tree."),

    ("Akıl yaşta değil, baştadır.",
     "Wisdom doesn't necessarily come with age."),

    ("Görünen köy kılavuz istemez.",
     "What is obvious needs no explanation."),

    ("Söz gümüşse sükût altındır.",
     "Speech is silver, silence is golden."),

    ("Her işte bir hayır vardır.",
     "Every cloud has a silver lining."),

    ("Bin ölçüp bir biçmeli.",
     "Measure twice, cut once."),

    ("Ak akçe kara gün içindir.",
     "Save for a rainy day."),

    ("Zararın neresinden dönülse kârdır.",
     "It is never too late to stop a loss."),

    ("İşleyen demir ışıldar.",
     "An active mind and body stay sharp."),

    ("Sabreden derviş muradına ermiş.",
     "Patience is a virtue."),

    ("Acele işe şeytan karışır.",
     "Haste makes waste."),

    ("Bugünün işini yarına bırakma.",
     "Never put off until tomorrow what you can do today."),

    ("Bir elin nesi var, iki elin sesi var.",
     "Many hands make light work."),

    ("Birlikten kuvvet doğar.",
     "Unity is strength."),

    ("Taşıma suyla değirmen dönmez.",
     "Temporary fixes cannot sustain a long-term process."),

    ("Lafla peynir gemisi yürümez.",
     "Actions speak louder than words."),

    ("Emek olmadan yemek olmaz.",
     "No pain, no gain."),

    ("İsteyenin bir yüzü, vermeyenin iki yüzü kara.",
     "If you don't ask, you don't get."),

    ("Dost kara günde belli olur.",
     "A friend in need is a friend indeed."),

    ("Gülü seven dikenine katlanır.",
     "He who loves the rose must endure its thorns."),

    ("Üzüm üzüme baka baka kararır.",
     "You become like the company you keep."),

    ("Ev alma, komşu al.",
     "Good neighbors are more important than a good house."),

    ("Komşu komşunun külüne muhtaçtır.",
     "Neighbors depend on one another, even for small things."),

    ("Tatlı dil yılanı deliğinden çıkarır.",
     "You can catch more flies with honey than with vinegar."),

    ("Gönül ferman dinlemez.",
     "The heart wants what it wants."),

    ("İnsan yedisinde ne ise yetmişinde de odur.",
     "A leopard cannot change its spots."),

    ("Körle yatan şaşı kalkar.",
     "If you lie down with dogs, you get up with fleas."),

    ("Bir fincan kahvenin kırk yıl hatırı vardır.",
     "A small kindness can be remembered for a lifetime."),

    ("Keskin sirke küpüne zarar.",
     "Anger often harms the person who harbors it."),

    ("Kelin ilacı olsa başına sürer.",
     "Physician, heal thyself."),

    ("Minareyi çalan kılıfını hazırlar.",
     "Someone planning wrongdoing prepares an excuse in advance."),

    ("Denize düşen yılana sarılır.",
     "A drowning person will clutch at a straw."),

    ("Davulun sesi uzaktan hoş gelir.",
     "The grass is always greener on the other side."),

    ("Her koyun kendi bacağından asılır.",
     "Everyone is responsible for their own actions."),

    ("Güneş balçıkla sıvanmaz.",
     "The truth cannot be hidden."),

    ("Akıl akıldan üstündür.",
     "Two heads are better than one."),

    ("Sürüden ayrılanı kurt kapar.",
     "There is safety in numbers."),

    ("Perşembenin gelişi çarşambadan bellidir.",
     "The writing is on the wall."),

    ("Ayağını yorganına göre uzat.",
     "Cut your coat according to your cloth."),

    ("Sakla samanı, gelir zamanı.",
     "Keep something because it may be useful later."),

    ("Bedava sirke baldan tatlıdır.",
     "Free things can seem especially appealing."),

    ("Ucuz etin yahnisi yavan olur.",
     "You get what you pay for."),

    ("İşten artmaz, dişten artar.",
     "Savings come from careful spending."),

    ("Borç yiğidin kamçısıdır.",
     "Debt can spur a person to work harder."),

    ("Hazıra dağ dayanmaz.",
     "Even great wealth will run out if you keep spending it."),

    ("Azıcık aşım, kaygısız başım.",
     "A modest living can bring peace of mind."),

    ("Üzümünü ye, bağını sorma.",
     "Enjoy the benefit without worrying about unnecessary details."),

    ("Sütten ağzı yanan yoğurdu üfleyerek yer.",
     "Once bitten, twice shy."),

    ("Ateş olmayan yerden duman çıkmaz.",
     "There is no smoke without fire."),

    ("Kaçan balık büyük olur.",
     "The one that got away is always the biggest."),

    ("Son pişmanlık fayda etmez.",
     "It is no use crying over spilled milk."),

    ("Eski dost düşman olmaz, yenisinden vefa gelmez.",
     "Old friends are often more dependable than new acquaintances."),

    ("Bir musibet bin nasihatten iyidir.",
     "Experience is the best teacher."),

    ("Sakınan göze çöp batar.",
     "Excessive worry can make things seem more likely to go wrong."),

    ("Korkunun ecele faydası yoktur.",
     "There is no point fearing the inevitable."),

    ("Yalancının mumu yatsıya kadar yanar.",
     "A lie cannot remain hidden forever."),

    ("Son gülen iyi güler.",
     "He who laughs last, laughs best."),

    ("Bal tutan parmağını yalar.",
     "Those who handle something desirable may benefit from it."),

    ("İki karpuz bir koltuğa sığmaz.",
     "You cannot do two difficult things at the same time."),
]


# =====================================================
# GENERATE MULTIPLE-CHOICE OPTIONS
# =====================================================

def build_questions():
    questions = []

    all_answers = list(dict.fromkeys(
        answer for _, answer in RAW_QUESTIONS
    ))

    for proverb, correct_answer in RAW_QUESTIONS:

        distractors = [
            answer
            for answer in all_answers
            if answer != correct_answer
        ]

        options = random.sample(
            distractors,
            min(3, len(distractors)),
        )

        options.append(correct_answer)
        random.shuffle(options)

        questions.append({
            "proverb": proverb,
            "answer": correct_answer,
            "options": options,
        })

    random.shuffle(questions)

    return questions


# =====================================================
# SESSION STATE
# =====================================================

def reset_quiz():
    st.session_state.questions = build_questions()
    st.session_state.current = 0
    st.session_state.answers = {}
    st.session_state.feedback_start = None
    st.session_state.finished = False
    st.session_state.result_saved = False


if "questions" not in st.session_state:
    reset_quiz()

if "player_name" not in st.session_state:
    st.session_state.player_name = "Player"


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
    st.write("- Select the correct English equivalent.")
    st.write("- Correct answers appear in green.")
    st.write("- Incorrect selections appear in red.")
    st.write("- Feedback lasts 3 seconds.")
    st.write("- The next question loads automatically.")

    if st.button("🔄 Restart Quiz", use_container_width=True):
        reset_quiz()
        st.rerun()


# =====================================================
# HEADER AND SCORE
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

questions = st.session_state.questions
current = st.session_state.current
total = len(questions)
answers = st.session_state.answers

score = sum(
    1
    for i, answer in answers.items()
    if answer == questions[i]["answer"]
)

col1, col2, col3 = st.columns(3)

col1.metric("Question", f"{min(current + 1, total)}/{total}")
col2.metric("Score", f"{score}/{total}")
col3.metric("Answered", f"{len(answers)}/{total}")

st.progress(len(answers) / total)

st.divider()


# =====================================================
# QUIZ SCREEN
# =====================================================

if not st.session_state.finished and current < total:

    question = questions[current]

    st.markdown(
        f'<div class="proverb">'
        f'🇹🇷 {question["proverb"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.write("**Choose the correct English equivalent:**")

    submitted_answer = answers.get(current)

    # -----------------------------------------------
    # BEFORE ANSWERING
    # -----------------------------------------------

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
                st.warning("Please select an answer.")

            else:
                st.session_state.answers[current] = selected
                st.session_state.feedback_start = time.time()
                st.rerun()

    # -----------------------------------------------
    # AFTER ANSWERING
    # -----------------------------------------------

    else:

        # Correct option is always green.
        # Selected wrong option is red.
        for option in question["options"]:

            if option == question["answer"]:

                st.markdown(
                    f'<div class="correct">'
                    f'✅ {option}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            elif option == submitted_answer:

                st.markdown(
                    f'<div class="wrong">'
                    f'❌ {option}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    f'<div class="neutral">'
                    f'{option}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        if submitted_answer == question["answer"]:
            st.success("Correct! 🎉")
        else:
            st.error("Incorrect! The correct answer is highlighted in green.")

        # -------------------------------------------
        # FAILSAFE AUTO-ADVANCE
        # -------------------------------------------

        if st.session_state.feedback_start is None:
            st.session_state.feedback_start = time.time()

        elapsed = time.time() - st.session_state.feedback_start
        remaining = 3 - elapsed

        if remaining > 0:

            st.caption(
                f"⏳ Moving to the next question in "
                f"{remaining:.1f} seconds..."
            )

            # No additional packages required.
            time.sleep(remaining)

        # Advance once the three-second feedback period ends.
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
        for i, answer in st.session_state.answers.items()
        if answer == st.session_state.questions[i]["answer"]
    )

    percentage = round(score / total * 100, 1)

    # Save the result once per completed quiz.
    if not st.session_state.result_saved:

        con.execute(
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

        con.commit()
        st.session_state.result_saved = True

    st.balloons()

    st.title("🏆 Quiz Completed!")

    col1, col2 = st.columns(2)

    col1.metric("Final Score", f"{score}/{total}")
    col2.metric("Percentage", f"{percentage}%")

    if percentage == 100:
        st.success("Perfect score! Mükemmel! 🇹🇷")
    elif percentage >= 80:
        st.success("Excellent work! Harika!")
    elif percentage >= 60:
        st.info("Good job! Keep learning.")
    elif percentage >= 40:
        st.warning("Good effort! Practice makes perfect.")
    else:
        st.info("Keep practicing. You will improve!")

    st.divider()

    st.subheader("📖 Review Your Answers")

    for i, question in enumerate(questions):

        user_answer = answers.get(i)
        correct_answer = question["answer"]

        with st.expander(
            f"{'✅' if user_answer == correct_answer else '❌'} "
            f"{i + 1}. {question['proverb']}"
        ):

            if user_answer == correct_answer:
                st.success(f"Your answer: {user_answer}")
            else:
                st.error(f"Your answer: {user_answer or 'Not answered'}")
                st.success(f"Correct answer: {correct_answer}")

    st.divider()

    st.subheader("📊 Recent Quiz Results")

    rows = con.execute(
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

    if rows:

        df = pd.DataFrame(
            rows,
            columns=[
                "Player",
                "Score",
                "Total",
                "Percentage",
                "Completed At",
            ],
        )

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
