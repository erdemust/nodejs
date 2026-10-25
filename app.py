import streamlit as st
import random

st.set_page_config(
    page_title="Turkish Proverbs Quiz",
    page_icon="🇹🇷",
    layout="centered"
)

QUESTIONS = [
    {
        "proverb": "Damlaya damlaya göl olur.",
        "answer": "Little by little, a little becomes a lot.",
        "options": [
            "Little by little, a little becomes a lot.",
            "Easy come, easy go.",
            "Actions speak louder than words.",
            "Time heals all wounds."
        ]
    },
    {
        "proverb": "Ne ekersen onu biçersin.",
        "answer": "You reap what you sow.",
        "options": [
            "Better late than never.",
            "You reap what you sow.",
            "Practice makes perfect.",
            "Look before you leap."
        ]
    },
    {
        "proverb": "Dost kara günde belli olur.",
        "answer": "A friend in need is a friend indeed.",
        "options": [
            "Opposites attract.",
            "Honesty is the best policy.",
            "A friend in need is a friend indeed.",
            "Two heads are better than one."
        ]
    },
    {
        "proverb": "Acele işe şeytan karışır.",
        "answer": "Haste makes waste.",
        "options": [
            "Where there's a will, there's a way.",
            "All's well that ends well.",
            "Time is money.",
            "Haste makes waste."
        ]
    },
    {
        "proverb": "Ayağını yorganına göre uzat.",
        "answer": "Cut your coat according to your cloth.",
        "options": [
            "Cut your coat according to your cloth.",
            "The early bird catches the worm.",
            "Don't count your chickens before they hatch.",
            "Make hay while the sun shines."
        ]
    },
    {
        "proverb": "Söz gümüşse sükût altındır.",
        "answer": "Speech is silver, silence is golden.",
        "options": [
            "Knowledge is power.",
            "Speech is silver, silence is golden.",
            "Practice what you preach.",
            "The pen is mightier than the sword."
        ]
    },
    {
        "proverb": "Sütten ağzı yanan yoğurdu üfleyerek yer.",
        "answer": "Once bitten, twice shy.",
        "options": [
            "Every cloud has a silver lining.",
            "Don't bite the hand that feeds you.",
            "Once bitten, twice shy.",
            "Two wrongs don't make a right."
        ]
    },
    {
        "proverb": "Tatlı dil yılanı deliğinden çıkarır.",
        "answer": "You can catch more flies with honey than with vinegar.",
        "options": [
            "Curiosity killed the cat.",
            "The squeaky wheel gets the grease.",
            "Fortune favors the bold.",
            "You can catch more flies with honey than with vinegar."
        ]
    },
    {
        "proverb": "Ateş olmayan yerden duman çıkmaz.",
        "answer": "There is no smoke without fire.",
        "options": [
            "There is no smoke without fire.",
            "Out of sight, out of mind.",
            "Still waters run deep.",
            "Every dog has its day."
        ]
    },
    {
        "proverb": "Gülü seven dikenine katlanır.",
        "answer": "He who loves the rose must endure its thorns.",
        "options": [
            "Birds of a feather flock together.",
            "He who loves the rose must endure its thorns.",
            "Absence makes the heart grow fonder.",
            "Beauty is in the eye of the beholder."
        ]
    }
]

# Initialize quiz state
if "questions" not in st.session_state:
    st.session_state.questions = QUESTIONS.copy()
    random.shuffle(st.session_state.questions)
    st.session_state.index = 0
    st.session_state.answers = {}
    st.session_state.finished = False

questions = st.session_state.questions
index = st.session_state.index
total = len(questions)

# Styling
st.markdown("""
<style>
.answer-button {
    padding: 12px 15px;
    border-radius: 10px;
    margin: 6px 0;
    border: 2px solid #cccccc;
    color: #222222;
    background-color: #ffffff;
    font-size: 16px;
}
.correct-answer {
    background-color: #d4edda;
    border: 2px solid #28a745;
    color: #155724;
    padding: 14px;
    border-radius: 10px;
    margin: 8px 0;
}
.wrong-answer {
    background-color: #f8d7da;
    border: 2px solid #dc3545;
    color: #721c24;
    padding: 14px;
    border-radius: 10px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

st.title("🇹🇷 Turkish Proverbs Quiz")
st.write("Choose the correct English equivalent.")

if not st.session_state.finished and index < total:

    q = questions[index]

    st.progress(index / total)
    st.subheader(f"Question {index + 1} of {total}")
    st.markdown(f"### 🇹🇷 {q['proverb']}")

    # Has this question already been answered?
    submitted_answer = st.session_state.answers.get(index)

    if submitted_answer is None:

        # Answer choices
        selected = st.radio(
            "Select your answer:",
            q["options"],
            key=f"answer_{index}",
            index=None
        )

        if st.button("Check Answer", type="primary"):
            if selected is None:
                st.warning("Please select an answer.")
            else:
                st.session_state.answers[index] = selected
                st.rerun()

    else:
        # Show all options on the SAME screen.
        # Correct option is green; selected wrong option is red.
        for option in q["options"]:

            if option == q["answer"]:
                st.markdown(
                    f'<div class="correct-answer">'
                    f'✅ {option}</div>',
                    unsafe_allow_html=True
                )

            elif option == submitted_answer:
                st.markdown(
                    f'<div class="wrong-answer">'
                    f'❌ {option}</div>',
                    unsafe_allow_html=True
                )

            else:
                st.markdown(
                    f'<div class="answer-button">'
                    f'{option}</div>',
                    unsafe_allow_html=True
                )

        if submitted_answer == q["answer"]:
            st.success("Correct! 🎉")
        else:
            st.error("Incorrect. The correct answer is highlighted in green.")

        # Continue without navigating to a separate feedback screen
        if index + 1 < total:
            if st.button("Next Question ➡️", type="primary"):
                st.session_state.index += 1
                st.rerun()
        else:
            if st.button("See Results 🏆", type="primary"):
                st.session_state.finished = True
                st.rerun()

# Final results
if st.session_state.finished:

    score = sum(
        1
        for i, q in enumerate(questions)
        if st.session_state.answers.get(i) == q["answer"]
    )

    st.balloons()
    st.title("🏆 Quiz Completed!")
    st.metric("Final Score", f"{score}/{total}")
    st.metric("Percentage", f"{round(score / total * 100)}%")

    if score == total:
        st.success("Perfect score! Excellent work!")
    elif score >= 7:
        st.success("Great job!")
    elif score >= 5:
        st.info("Good effort! Keep practicing.")
    else:
        st.warning("Keep learning. You'll improve with practice!")

    st.subheader("Answer Review")

    for i, q in enumerate(questions):
        user_answer = st.session_state.answers.get(i)

        with st.expander(f"{i + 1}. {q['proverb']}"):
            if user_answer == q["answer"]:
                st.success(f"Your answer: {user_answer}")
            else:
                st.error(f"Your answer: {user_answer}")
                st.success(f"Correct answer: {q['answer']}")

    if st.button("🔄 Restart Quiz", type="primary"):
        for key in ["questions", "index", "answers", "finished"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
