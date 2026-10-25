import streamlit as st
import random

st.set_page_config(
    page_title="Turkish Proverbs Quiz",
    page_icon="🇹🇷",
    layout="centered"
)

# -----------------------------------
# Quiz questions
# -----------------------------------
QUESTIONS = [
    {
        "proverb": "Damlaya damlaya göl olur.",
        "question": "What is the English equivalent?",
        "options": [
            "Little by little, a little becomes a lot.",
            "Easy come, easy go.",
            "Actions speak louder than words.",
            "Time heals all wounds."
        ],
        "answer": "Little by little, a little becomes a lot.",
        "meaning": "Small amounts accumulate over time into something substantial."
    },
    {
        "proverb": "Ne ekersen onu biçersin.",
        "question": "What is the English equivalent?",
        "options": [
            "Better late than never.",
            "You reap what you sow.",
            "Practice makes perfect.",
            "Look before you leap."
        ],
        "answer": "You reap what you sow.",
        "meaning": "Your actions determine the results you experience."
    },
    {
        "proverb": "Dost kara günde belli olur.",
        "question": "What is the English equivalent?",
        "options": [
            "Opposites attract.",
            "Honesty is the best policy.",
            "A friend in need is a friend indeed.",
            "Two heads are better than one."
        ],
        "answer": "A friend in need is a friend indeed.",
        "meaning": "A genuine friend supports you during difficult times."
    },
    {
        "proverb": "Acele işe şeytan karışır.",
        "question": "What is the English equivalent?",
        "options": [
            "Where there's a will, there's a way.",
            "All's well that ends well.",
            "Time is money.",
            "Haste makes waste."
        ],
        "answer": "Haste makes waste.",
        "meaning": "Rushing often causes mistakes and extra work."
    },
    {
        "proverb": "Ayağını yorganına göre uzat.",
        "question": "What is the English equivalent?",
        "options": [
            "Cut your coat according to your cloth.",
            "The early bird catches the worm.",
            "Don't count your chickens before they hatch.",
            "Make hay while the sun shines."
        ],
        "answer": "Cut your coat according to your cloth.",
        "meaning": "Live within your means and adjust spending to your resources."
    },
    {
        "proverb": "Söz gümüşse sükût altındır.",
        "question": "What is the English equivalent?",
        "options": [
            "Knowledge is power.",
            "Speech is silver, silence is golden.",
            "Practice what you preach.",
            "The pen is mightier than the sword."
        ],
        "answer": "Speech is silver, silence is golden.",
        "meaning": "Sometimes remaining silent is wiser than speaking."
    },
    {
        "proverb": "Sütten ağzı yanan yoğurdu üfleyerek yer.",
        "question": "What is the English equivalent?",
        "options": [
            "Every cloud has a silver lining.",
            "Don't bite the hand that feeds you.",
            "Once bitten, twice shy.",
            "Two wrongs don't make a right."
        ],
        "answer": "Once bitten, twice shy.",
        "meaning": "A bad experience makes people more cautious in similar situations."
    },
    {
        "proverb": "Tatlı dil yılanı deliğinden çıkarır.",
        "question": "What is the English equivalent?",
        "options": [
            "Curiosity killed the cat.",
            "The squeaky wheel gets the grease.",
            "Fortune favors the bold.",
            "You can catch more flies with honey than with vinegar."
        ],
        "answer": "You can catch more flies with honey than with vinegar.",
        "meaning": "Kind words can persuade people more effectively than harshness."
    },
    {
        "proverb": "Ateş olmayan yerden duman çıkmaz.",
        "question": "What is the English equivalent?",
        "options": [
            "There is no smoke without fire.",
            "Out of sight, out of mind.",
            "Still waters run deep.",
            "Every dog has its day."
        ],
        "answer": "There is no smoke without fire.",
        "meaning": "Signs or rumors may have an underlying cause."
    },
    {
        "proverb": "Gülü seven dikenine katlanır.",
        "question": "What is the English equivalent?",
        "options": [
            "Birds of a feather flock together.",
            "He who loves the rose must endure its thorns.",
            "Absence makes the heart grow fonder.",
            "Beauty is in the eye of the beholder."
        ],
        "answer": "He who loves the rose must endure its thorns.",
        "meaning": "Valuable things often come with difficulties we must accept."
    }
]

# -----------------------------------
# Initialize session state
# -----------------------------------
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = QUESTIONS.copy()
    random.shuffle(st.session_state.quiz_questions)

if "current_question" not in st.session_state:
    st.session_state.current_question = 0

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "submitted" not in st.session_state:
    st.session_state.submitted = {}

# -----------------------------------
# Header
# -----------------------------------
st.title("🇹🇷 Turkish Proverbs Quiz")
st.write(
    "Test your knowledge of Turkish proverbs and their "
    "English equivalents!"
)

st.divider()

questions = st.session_state.quiz_questions
total = len(questions)
index = st.session_state.current_question

# -----------------------------------
# Score calculation
# -----------------------------------
score = sum(
    1
    for i, answer in st.session_state.answers.items()
    if answer == questions[i]["answer"]
)

answered = len(st.session_state.answers)

col1, col2, col3 = st.columns(3)

col1.metric("Question", f"{min(index + 1, total)}/{total}")
col2.metric("Score", f"{score}/{total}")
col3.metric("Answered", f"{answered}/{total}")

st.progress(answered / total)

st.divider()

# -----------------------------------
# Display current question
# -----------------------------------
if index < total:
    q = questions[index]

    st.subheader(f"Question {index + 1}")
    st.markdown(f"### 🇹🇷 {q['proverb']}")
    st.write(q["question"])

    # If already answered, preserve the answer.
    previous_answer = st.session_state.answers.get(index)

    if previous_answer is None:
        selected = st.radio(
            "Choose the correct English equivalent:",
            q["options"],
            key=f"choice_{index}",
            index=None
        )

        if st.button("Submit Answer", type="primary"):
            if selected is None:
                st.warning("Please select an answer first.")
            else:
                st.session_state.answers[index] = selected
                st.session_state.submitted[index] = True
                st.rerun()

    else:
        # Show the saved answer and feedback.
        for option in q["options"]:
            if option == q["answer"]:
                st.success(f"✅ {option} — Correct answer")
            elif option == previous_answer:
                st.error(f"❌ {option} — Your answer")

        if previous_answer == q["answer"]:
            st.success("Correct! 🎉")
        else:
            st.error("Not quite! Here is the correct answer:")
            st.success(f"✅ {q['answer']}")

        st.info(f"💡 Meaning: {q['meaning']}")

        if index < total - 1:
            if st.button("Next Question ➡️", type="primary"):
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("See Final Results 🏆", type="primary"):
                st.session_state.current_question += 1
                st.rerun()

# -----------------------------------
# Final results
# -----------------------------------
else:
    st.balloons()

    st.title("🏆 Quiz Completed!")

    percentage = round((score / total) * 100)

    st.metric("Final Score", f"{score}/{total}")
    st.metric("Percentage", f"{percentage}%")

    if percentage == 100:
        st.success("Perfect score! Excellent knowledge of Turkish proverbs!")
    elif percentage >= 70:
        st.success("Great job! You know your Turkish proverbs well!")
    elif percentage >= 50:
        st.info("Good effort! A little more practice will help.")
    else:
        st.warning("Keep practicing! You'll improve with every attempt.")

    st.subheader("Review Your Answers")

    for i, q in enumerate(questions):
        user_answer = st.session_state.answers.get(i)

        with st.expander(f"{i + 1}. {q['proverb']}"):
            if user_answer == q["answer"]:
                st.success(f"Your answer: {user_answer}")
            else:
                st.error(f"Your answer: {user_answer or 'Not answered'}")
                st.success(f"Correct answer: {q['answer']}")

            st.write(f"Meaning: {q['meaning']}")

    if st.button("🔄 Restart Quiz", type="primary"):
        st.session_state.quiz_questions = QUESTIONS.copy()
        random.shuffle(st.session_state.quiz_questions)
        st.session_state.current_question = 0
        st.session_state.answers = {}
        st.session_state.submitted = {}
        st.rerun()
