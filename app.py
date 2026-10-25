import random
import sqlite3
import time
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Turkish Proverbs Quiz",
    page_icon="🇹🇷",
    layout="centered",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
    .main-title {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 800;
        color: #D71920;
        margin-bottom: 0;
    }

    .subtitle {
        text-align: center;
        color: #777777;
        margin-bottom: 25px;
    }

    .proverb-box {
        background-color: #f5f5f5;
        border-left: 6px solid #D71920;
        padding: 20px;
        border-radius: 10px;
        margin: 18px 0;
        font-size: 1.35rem;
        font-weight: 600;
        color: #222222;
    }

    .answer {
        padding: 14px 16px;
        margin: 8px 0;
        border-radius: 10px;
        border: 2px solid #dddddd;
        background-color: #ffffff;
        color: #222222;
        font-size: 1rem;
    }

    .correct-answer {
        background-color: #d4edda;
        border: 2px solid #28a745;
        color: #155724;
        padding: 14px 16px;
        margin: 8px 0;
        border-radius: 10px;
        font-size: 1rem;
        font-weight: 600;
    }

    .wrong-answer {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        color: #721c24;
        padding: 14px 16px;
        margin: 8px 0;
        border-radius: 10px;
        font-size: 1rem;
        font-weight: 600;
    }

    .timer-box {
        text-align: center;
        font-size: 1.05rem;
        font-weight: 600;
        color: #555555;
        padding: 8px;
    }

    .score-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }

    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 42px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE
# =========================================================

@st.cache_resource
def get_connection():
    connection = sqlite3.connect(
        "proverbs_quiz.db",
        check_same_thread=False,
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            completed_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    return connection


con = get_connection()


# =========================================================
# TURKISH PROVERBS QUESTION BANK
# =========================================================

QUESTIONS = [
    {
        "proverb": "Damlaya damlaya göl olur.",
        "answer": "Little by little, a little becomes a lot.",
        "meaning": "Small amounts accumulate over time into something substantial.",
        "options": [
            "Little by little, a little becomes a lot.",
            "Easy come, easy go.",
            "Actions speak louder than words.",
            "Time heals all wounds.",
        ],
    },
    {
        "proverb": "Ne ekersen onu biçersin.",
        "answer": "You reap what you sow.",
        "meaning": "Your actions determine the results you experience.",
        "options": [
            "Better late than never.",
            "You reap what you sow.",
            "Practice makes perfect.",
            "Look before you leap.",
        ],
    },
    {
        "proverb": "Ağaç yaşken eğilir.",
        "answer": "As the twig is bent, so grows the tree.",
        "meaning": "It is easier to teach good habits and values to children.",
        "options": [
            "A rolling stone gathers no moss.",
            "As the twig is bent, so grows the tree.",
            "Every dog has its day.",
            "Better safe than sorry.",
        ],
    },
    {
        "proverb": "Akıl yaşta değil, baştadır.",
        "answer": "Wisdom doesn't necessarily come with age.",
        "meaning": "Intelligence and wisdom matter more than a person's age.",
        "options": [
            "Age is just a number.",
            "Experience is the best teacher.",
            "Wisdom doesn't necessarily come with age.",
            "You can't teach an old dog new tricks.",
        ],
    },
    {
        "proverb": "Görünen köy kılavuz istemez.",
        "answer": "What is obvious needs no explanation.",
        "meaning": "Something clearly visible or evident needs no guidance.",
        "options": [
            "What is obvious needs no explanation.",
            "Don't judge a book by its cover.",
            "Appearances can be deceiving.",
            "All that glitters is not gold.",
        ],
    },
    {
        "proverb": "Söz gümüşse sükût altındır.",
        "answer": "Speech is silver, silence is golden.",
        "meaning": "Sometimes it is wiser to remain silent than to speak.",
        "options": [
            "Knowledge is power.",
            "Speech is silver, silence is golden.",
            "Actions speak louder than words.",
            "The pen is mightier than the sword.",
        ],
    },
    {
        "proverb": "Her işte bir hayır vardır.",
        "answer": "Every cloud has a silver lining.",
        "meaning": "Something good may come from an apparently bad situation.",
        "options": [
            "Every cloud has a silver lining.",
            "No pain, no gain.",
            "Time waits for no one.",
            "Practice makes perfect.",
        ],
    },
    {
        "proverb": "Bin ölçüp bir biçmeli.",
        "answer": "Measure twice, cut once.",
        "meaning": "Think and check carefully before taking action.",
        "options": [
            "Strike while the iron is hot.",
            "Measure twice, cut once.",
            "Time is money.",
            "Don't put all your eggs in one basket.",
        ],
    },
    {
        "proverb": "Ak akçe kara gün içindir.",
        "answer": "Save for a rainy day.",
        "meaning": "Save money for difficult times in the future.",
        "options": [
            "Money doesn't grow on trees.",
            "Easy come, easy go.",
            "Save for a rainy day.",
            "Time is money.",
        ],
    },
    {
        "proverb": "Zararın neresinden dönülse kârdır.",
        "answer": "It is never too late to stop a loss.",
        "meaning": "Stopping a bad decision is beneficial, even if some damage has already occurred.",
        "options": [
            "No use crying over spilled milk.",
            "It is never too late to stop a loss.",
            "Nothing ventured, nothing gained.",
            "The show must go on.",
        ],
    },
    {
        "proverb": "İşleyen demir ışıldar.",
        "answer": "An active mind and body stay sharp.",
        "meaning": "Regular activity and practice help maintain one's abilities.",
        "options": [
            "An active mind and body stay sharp.",
            "Slow and steady wins the race.",
            "All work and no play makes Jack a dull boy.",
            "Rome wasn't built in a day.",
        ],
    },
    {
        "proverb": "Sabreden derviş muradına ermiş.",
        "answer": "Patience is a virtue.",
        "meaning": "Patience and perseverance can eventually lead to success.",
        "options": [
            "Fortune favors the bold.",
            "Patience is a virtue.",
            "Time is money.",
            "The early bird catches the worm.",
        ],
    },
    {
        "proverb": "Acele işe şeytan karışır.",
        "answer": "Haste makes waste.",
        "meaning": "Rushing often causes mistakes and extra work.",
        "options": [
            "Haste makes waste.",
            "Better late than never.",
            "Where there's a will, there's a way.",
            "Time flies when you're having fun.",
        ],
    },
    {
        "proverb": "Bugünün işini yarına bırakma.",
        "answer": "Never put off until tomorrow what you can do today.",
        "meaning": "Complete your tasks promptly rather than procrastinating.",
        "options": [
            "Good things come to those who wait.",
            "Never put off until tomorrow what you can do today.",
            "Tomorrow is another day.",
            "Look before you leap.",
        ],
    },
    {
        "proverb": "Bir elin nesi var, iki elin sesi var.",
        "answer": "Many hands make light work.",
        "meaning": "Cooperation makes difficult tasks easier.",
        "options": [
            "Too many cooks spoil the broth.",
            "Many hands make light work.",
            "Every man for himself.",
            "Practice makes perfect.",
        ],
    },
    {
        "proverb": "Birlikten kuvvet doğar.",
        "answer": "Unity is strength.",
        "meaning": "People are stronger when they work together.",
        "options": [
            "Unity is strength.",
            "Knowledge is power.",
            "Silence is golden.",
            "Time is money.",
        ],
    },
    {
        "proverb": "Taşıma suyla değirmen dönmez.",
        "answer": "Temporary fixes cannot sustain a long-term process.",
        "meaning": "Lasting success requires a reliable and sustainable source of support.",
        "options": [
            "All good things must come to an end.",
            "Temporary fixes cannot sustain a long-term process.",
            "Every little bit helps.",
            "Where there's smoke, there's fire.",
        ],
    },
    {
        "proverb": "Lafla peynir gemisi yürümez.",
        "answer": "Actions speak louder than words.",
        "meaning": "Talk alone does not accomplish anything; action is necessary.",
        "options": [
            "Actions speak louder than words.",
            "Speech is silver, silence is golden.",
            "Honesty is the best policy.",
            "The pen is mightier than the sword.",
        ],
    },
    {
        "proverb": "Emek olmadan yemek olmaz.",
        "answer": "No pain, no gain.",
        "meaning": "Success and rewards require effort.",
        "options": [
            "Easy come, easy go.",
            "No pain, no gain.",
            "Practice makes perfect.",
            "Good things come to those who wait.",
        ],
    },
    {
        "proverb": "İsteyenin bir yüzü, vermeyenin iki yüzü kara.",
        "answer": "If you don't ask, you don't get.",
        "meaning": "You may miss opportunities if you never ask for what you need.",
        "options": [
            "If you don't ask, you don't get.",
            "Look before you leap.",
            "Silence is golden.",
            "The best things in life are free.",
        ],
    },
    {
        "proverb": "Dost kara günde belli olur.",
        "answer": "A friend in need is a friend indeed.",
        "meaning": "A genuine friend shows loyalty during difficult times.",
        "options": [
            "Opposites attract.",
            "A friend in need is a friend indeed.",
            "Good fences make good neighbors.",
            "Birds of a feather flock together.",
        ],
    },
    {
        "proverb": "Gülü seven dikenine katlanır.",
        "answer": "He who loves the rose must endure its thorns.",
        "meaning": "Good things often come with difficulties that must be accepted.",
        "options": [
            "Beauty is in the eye of the beholder.",
            "He who loves the rose must endure its thorns.",
            "Absence makes the heart grow fonder.",
            "Every rose has its day.",
        ],
    },
    {
        "proverb": "Üzüm üzüme baka baka kararır.",
        "answer": "You become like the company you keep.",
        "meaning": "People tend to adopt the habits and behavior of those around them.",
        "options": [
            "Opposites attract.",
            "You become like the company you keep.",
            "Practice makes perfect.",
            "Two heads are better than one.",
        ],
    },
    {
        "proverb": "Ev alma, komşu al.",
        "answer": "Good neighbors are more important than a good house.",
        "meaning": "A good neighborhood can matter more than the property itself.",
        "options": [
            "Home is where the heart is.",
            "Good neighbors are more important than a good house.",
            "East or west, home is best.",
            "Good fences make good neighbors.",
        ],
    },
    {
        "proverb": "Komşu komşunun külüne muhtaçtır.",
        "answer": "Neighbors depend on one another, even for small things.",
        "meaning": "People living near each other can benefit from mutual support.",
        "options": [
            "Every man for himself.",
            "Neighbors depend on one another, even for small things.",
            "Absence makes the heart grow fonder.",
            "Blood is thicker than water.",
        ],
    },
    {
        "proverb": "Tatlı dil yılanı deliğinden çıkarır.",
        "answer": "You can catch more flies with honey than with vinegar.",
        "meaning": "Kindness and tact can persuade people more effectively than hostility.",
        "options": [
            "Honesty is the best policy.",
            "You can catch more flies with honey than with vinegar.",
            "Silence is golden.",
            "The squeaky wheel gets the grease.",
        ],
    },
    {
        "proverb": "Gönül ferman dinlemez.",
        "answer": "The heart wants what it wants.",
        "meaning": "Love and emotions do not always obey reason or commands.",
        "options": [
            "Love conquers all.",
            "The heart wants what it wants.",
            "Out of sight, out of mind.",
            "Time heals all wounds.",
        ],
    },
    {
        "proverb": "İnsan yedisinde ne ise yetmişinde de odur.",
        "answer": "A leopard cannot change its spots.",
        "meaning": "A person's fundamental character tends to remain the same.",
        "options": [
            "You can't teach an old dog new tricks.",
            "A leopard cannot change its spots.",
            "Age brings wisdom.",
            "Appearances can be deceiving.",
        ],
    },
    {
        "proverb": "Körle yatan şaşı kalkar.",
        "answer": "If you lie down with dogs, you get up with fleas.",
        "meaning": "The people around you can influence your behavior and reputation.",
        "options": [
            "If you lie down with dogs, you get up with fleas.",
            "Birds of a feather flock together.",
            "Keep your friends close and your enemies closer.",
            "Two wrongs don't make a right.",
        ],
    },
    {
        "proverb": "Bir fincan kahvenin kırk yıl hatırı vardır.",
        "answer": "A small kindness can be remembered for a lifetime.",
        "meaning": "Hospitality and generosity can create lasting bonds of gratitude.",
        "options": [
            "There's no place like home.",
            "A small kindness can be remembered for a lifetime.",
            "Time heals all wounds.",
            "Blood is thicker than water.",
        ],
    },
    {
        "proverb": "Keskin sirke küpüne zarar.",
        "answer": "Anger often harms the person who harbors it.",
        "meaning": "Excessive anger can hurt the angry person as much as anyone else.",
        "options": [
            "Revenge is a dish best served cold.",
            "Anger often harms the person who harbors it.",
            "Honesty is the best policy.",
            "The truth will set you free.",
        ],
    },
    {
        "proverb": "Kelin ilacı olsa başına sürer.",
        "answer": "Physician, heal thyself.",
        "meaning": "People who cannot solve their own problems may not be able to solve others' problems.",
        "options": [
            "Practice makes perfect.",
            "Physician, heal thyself.",
            "Charity begins at home.",
            "Prevention is better than cure.",
        ],
    },
    {
        "proverb": "Minareyi çalan kılıfını hazırlar.",
        "answer": "Someone planning wrongdoing prepares an excuse in advance.",
        "meaning": "A person planning a serious deception may prepare a cover story beforehand.",
        "options": [
            "Honesty is the best policy.",
            "Someone planning wrongdoing prepares an excuse in advance.",
            "The truth will set you free.",
            "Crime doesn't pay.",
        ],
    },
    {
        "proverb": "Denize düşen yılana sarılır.",
        "answer": "A drowning person will clutch at a straw.",
        "meaning": "Desperate people may accept help from unlikely or undesirable sources.",
        "options": [
            "A drowning person will clutch at a straw.",
            "Look before you leap.",
            "Still waters run deep.",
            "Better safe than sorry.",
        ],
    },
    {
        "proverb": "Davulun sesi uzaktan hoş gelir.",
        "answer": "The grass is always greener on the other side.",
        "meaning": "Other people's situations often appear more attractive from a distance.",
        "options": [
            "Home is where the heart is.",
            "The grass is always greener on the other side.",
            "Every cloud has a silver lining.",
            "Distance makes the heart grow fonder.",
        ],
    },
    {
        "proverb": "Her koyun kendi bacağından asılır.",
        "answer": "Everyone is responsible for their own actions.",
        "meaning": "Each person must bear the consequences of their own behavior.",
        "options": [
            "United we stand, divided we fall.",
            "Everyone is responsible for their own actions.",
            "Two heads are better than one.",
            "No man is an island.",
        ],
    },
    {
        "proverb": "Güneş balçıkla sıvanmaz.",
        "answer": "The truth cannot be hidden.",
        "meaning": "Obvious facts cannot be concealed forever.",
        "options": [
            "The truth cannot be hidden.",
            "Out of sight, out of mind.",
            "Appearances can be deceiving.",
            "Silence is golden.",
        ],
    },
    {
        "proverb": "Akıl akıldan üstündür.",
        "answer": "Two heads are better than one.",
        "meaning": "Another person's perspective may offer a better solution.",
        "options": [
            "Knowledge is power.",
            "Two heads are better than one.",
            "Practice makes perfect.",
            "Silence is golden.",
        ],
    },
    {
        "proverb": "Sürüden ayrılanı kurt kapar.",
        "answer": "There is safety in numbers.",
        "meaning": "Staying with a group can offer protection.",
        "options": [
            "There is safety in numbers.",
            "Fortune favors the bold.",
            "Every man for himself.",
            "The early bird catches the worm.",
        ],
    },
    {
        "proverb": "Perşembenin gelişi çarşambadan bellidir.",
        "answer": "The writing is on the wall.",
        "meaning": "The likely outcome can often be predicted from early signs.",
        "options": [
            "Better late than never.",
            "The writing is on the wall.",
            "Time will tell.",
            "Never judge a book by its cover.",
        ],
    },
    {
        "proverb": "Ayağını yorganına göre uzat.",
        "answer": "Cut your coat according to your cloth.",
        "meaning": "Adjust your spending and expectations to match your resources.",
        "options": [
            "Money doesn't grow on trees.",
            "Cut your coat according to your cloth.",
            "The best things in life are free.",
            "Easy come, easy go.",
        ],
    },
    {
        "proverb": "Sakla samanı, gelir zamanı.",
        "answer": "Keep something because it may be useful later.",
        "meaning": "Even something that seems unimportant may become useful in the future.",
        "options": [
            "Out of sight, out of mind.",
            "Keep something because it may be useful later.",
            "Time is money.",
            "Waste not, want not.",
        ],
    },
    {
        "proverb": "Bedava sirke baldan tatlıdır.",
        "answer": "Free things can seem especially appealing.",
        "meaning": "People often value something because it costs them nothing.",
        "options": [
            "You get what you pay for.",
            "Free things can seem especially appealing.",
            "Money can't buy happiness.",
            "The best things in life are free.",
        ],
    },
    {
        "proverb": "Ucuz etin yahnisi yavan olur.",
        "answer": "You get what you pay for.",
        "meaning": "Very cheap products or services may be poor in quality.",
        "options": [
            "You get what you pay for.",
            "Time is money.",
            "Easy come, easy go.",
            "Waste not, want not.",
        ],
    },
    {
        "proverb": "Hazıra dağ dayanmaz.",
        "answer": "Even great wealth will run out if you keep spending it.",
        "meaning": "Resources are eventually exhausted if you rely on them without replenishing them.",
        "options": [
            "Money can't buy happiness.",
            "Even great wealth will run out if you keep spending it.",
            "Easy come, easy go.",
            "Save for a rainy day.",
        ],
    },
    {
        "proverb": "Azıcık aşım, kaygısız başım.",
        "answer": "A modest living can bring peace of mind.",
        "meaning": "A simple life with fewer worries can be preferable to wealth and stress.",
        "options": [
            "The more, the merrier.",
            "A modest living can bring peace of mind.",
            "Money makes the world go round.",
            "Time is money.",
        ],
    },
    {
        "proverb": "Üzümünü ye, bağını sorma.",
        "answer": "Enjoy the benefit without worrying about unnecessary details.",
        "meaning": "Focus on the benefit rather than asking unnecessary questions about its source.",
        "options": [
            "Honesty is the best policy.",
            "Enjoy the benefit without worrying about unnecessary details.",
            "Look before you leap.",
            "Don't count your chickens before they hatch.",
        ],
    },
    {
        "proverb": "Sütten ağzı yanan yoğurdu üfleyerek yer.",
        "answer": "Once bitten, twice shy.",
        "meaning": "After a bad experience, people become more cautious about similar situations.",
        "options": [
            "Once bitten, twice shy.",
            "Practice makes perfect.",
            "No pain, no gain.",
            "Every cloud has a silver lining.",
        ],
    },
    {
        "proverb": "Ateş olmayan yerden duman çıkmaz.",
        "answer": "There is no smoke without fire.",
        "meaning": "Rumors or signs may indicate an underlying cause.",
        "options": [
            "Where there's a will, there's a way.",
            "There is no smoke without fire.",
            "Out of sight, out of mind.",
            "Still waters run deep.",
        ],
    },
    {
        "proverb": "Kaçan balık büyük olur.",
        "answer": "The one that got away is always the biggest.",
        "meaning": "People tend to exaggerate the value of opportunities they have missed.",
        "options": [
            "The early bird catches the worm.",
            "The one that got away is always the biggest.",
            "Big fish eat little fish.",
            "Don't count your chickens before they hatch.",
        ],
    },
    {
        "proverb": "Son pişmanlık fayda etmez.",
        "answer": "It is no use crying over spilled milk.",
        "meaning": "Regret cannot undo what has already happened.",
        "options": [
            "Better late than never.",
            "It is no use crying over spilled milk.",
            "Time heals all wounds.",
            "Look before you leap.",
        ],
    },
    {
        "proverb": "Bir musibet bin nasihatten iyidir.",
        "answer": "Experience is the best teacher.",
        "meaning": "A difficult experience can teach more than repeated advice.",
        "options": [
            "Experience is the best teacher.",
            "Knowledge is power.",
            "Practice makes perfect.",
            "Better safe than sorry.",
        ],
    },
    {
        "proverb": "Korkunun ecele faydası yoktur.",
        "answer": "There is no point fearing the inevitable.",
        "meaning": "Worrying cannot prevent something that cannot be avoided.",
        "options": [
            "Fortune favors the bold.",
            "There is no point fearing the inevitable.",
            "Better safe than sorry.",
            "Every cloud has a silver lining.",
        ],
    },
    {
        "proverb": "Yalancının mumu yatsıya kadar yanar.",
        "answer": "A lie cannot remain hidden forever.",
        "meaning": "Deception is eventually exposed.",
        "options": [
            "Honesty is the best policy.",
            "A lie cannot remain hidden forever.",
            "Silence is golden.",
            "Actions speak louder than words.",
        ],
    },
    {
        "proverb": "Son gülen iyi güler.",
        "answer": "He who laughs last, laughs best.",
        "meaning": "The final outcome matters more than early appearances.",
        "options": [
            "Laughter is the best medicine.",
            "He who laughs last, laughs best.",
            "Every dog has its day.",
            "Fortune favors the bold.",
        ],
    },
]


# =========================================================
# SESSION STATE
# =========================================================

def initialize_quiz():
    shuffled_questions = []

    for original in QUESTIONS:
        question = original.copy()
        question["options"] = original["options"].copy()
        random.shuffle(question["options"])
        shuffled_questions.append(question)

    random.shuffle(shuffled_questions)

    st.session_state.questions = shuffled_questions
    st.session_state.current = 0
    st.session_state.answers = {}
    st.session_state.feedback_started = None
    st.session_state.finished = False
    st.session_state.saved_result = False


if "questions" not in st.session_state:
    initialize_quiz()

if "player_name" not in st.session_state:
    st.session_state.player_name = "Player"


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.header("⚙️ Quiz Settings")

    st.text_input(
        "Player name",
        key="player_name",
        max_chars=50,
    )

    st.divider()

    st.write("### 📚 About the Quiz")
    st.write(
        "Learn Turkish proverbs and discover their English equivalents."
    )

    st.write("### 🎯 Rules")
    st.write("- Select one answer per question.")
    st.write("- Correct answers turn green.")
    st.write("- Wrong selections turn red.")
    st.write("- Feedback lasts 3 seconds.")
    st.write("- The next question loads automatically.")

    st.divider()

    if st.button("🔄 Restart Quiz", use_container_width=True):
        initialize_quiz()
        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🇹🇷 Turkish Proverbs Quiz</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Discover Turkish wisdom, one proverb at a time!'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# QUIZ STATISTICS
# =========================================================

questions = st.session_state.questions
total = len(questions)
current = st.session_state.current
answers = st.session_state.answers

score = sum(
    1
    for i, answer in answers.items()
    if answer == questions[i]["answer"]
)

answered_count = len(answers)

col1, col2, col3 = st.columns(3)

col1.metric(
    "📝 Question",
    f"{min(current + 1, total)}/{total}",
)

col2.metric(
    "🏆 Score",
    f"{score}/{total}",
)

col3.metric(
    "✅ Answered",
    f"{answered_count}/{total}",
)

st.progress(answered_count / total if total else 0)

st.divider()


# =========================================================
# QUESTION DISPLAY
# =========================================================

if not st.session_state.finished and current < total:

    q = questions[current]

    st.markdown(
        f'<div class="proverb-box">🇹🇷 {q["proverb"]}</div>',
        unsafe_allow_html=True,
    )

    st.write("**Choose the correct English equivalent:**")

    selected_answer = answers.get(current)

    # -----------------------------------------------------
    # QUESTION NOT YET ANSWERED
    # -----------------------------------------------------

    if selected_answer is None:

        selected = st.radio(
            "Answer choices",
            q["options"],
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
                st.warning("Please select an answer first.")

            else:
                st.session_state.answers[current] = selected
                st.session_state.feedback_started = time.time()
                st.rerun()

    # -----------------------------------------------------
    # ANSWER SUBMITTED: COLOR THE OPTIONS
    # -----------------------------------------------------

    else:

        for option in q["options"]:

            if option == q["answer"]:

                st.markdown(
                    f'<div class="correct-answer">'
                    f'✅ {option}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            elif option == selected_answer:

                st.markdown(
                    f'<div class="wrong-answer">'
                    f'❌ {option}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    f'<div class="answer">'
                    f'{option}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # -------------------------------------------------
        # FEEDBACK
        # -------------------------------------------------

        if selected_answer == q["answer"]:

            st.success("Correct! 🎉")

        else:

            st.error("Incorrect! The correct answer is highlighted in green.")

        st.info(f"💡 {q['meaning']}")

        # -------------------------------------------------
        # AUTOMATIC NEXT QUESTION
        # -------------------------------------------------

        if st.session_state.feedback_started is None:
            st.session_state.feedback_started = time.time()

        elapsed = time.time() - st.session_state.feedback_started
        remaining = max(0, 3 - elapsed)

        if remaining > 0:

            st.markdown(
                f'<div class="timer-box">'
                f'Next question in {remaining:.1f} seconds...'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Refresh the page every 200 ms so the countdown updates.
            st_autorefresh(
                interval=200,
                limit=20,
                key=f"timer_{current}",
            )

        else:

            if current + 1 < total:

                st.session_state.current += 1
                st.session_state.feedback_started = None
                st.rerun()

            else:

                st.session_state.finished = True
                st.rerun()


# =========================================================
# FINAL RESULTS
# =========================================================

if st.session_state.finished:

    # Save the completed attempt only once.
    if not st.session_state.saved_result:

        percentage = round(score / total * 100, 2)

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
        st.session_state.saved_result = True

    percentage = round(score / total * 100)

    st.balloons()

    st.title("🏆 Quiz Completed!")

    st.metric("Final Score", f"{score}/{total}")
    st.metric("Percentage", f"{percentage}%")

    if percentage == 100:
        st.success("Perfect score! Mükemmel! 🇹🇷")

    elif percentage >= 80:
        st.success("Excellent work! Harika!")

    elif percentage >= 60:
        st.info("Good job! Keep learning Turkish.")

    elif percentage >= 40:
        st.warning("Good effort! Practice makes perfect.")

    else:
        st.warning("Keep practicing. You will improve!")

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

            st.write(f"**Meaning:** {question['meaning']}")

    st.divider()

    st.subheader("📊 Recent Quiz Results")

    results = con.execute(
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

    if results:

        import pandas as pd

        results_df = pd.DataFrame(
            results,
            columns=[
                "Player",
                "Score",
                "Total",
                "Percentage",
                "Completed At",
            ],
        )

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True,
        )

    if st.button(
        "🔄 Play Again",
        type="primary",
        use_container_width=True,
    ):

        initialize_quiz()
        st.rerun()
