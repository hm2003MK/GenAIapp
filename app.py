import streamlit as st
import requests
import json

# ===== CONFIG =====
BASE_URL = "https://hearmelam.app.n8n.cloud/webhook"

# --- Webhook endpoints (from your n8n nodes) ---
WEBHOOKS = {
    "teacher": f"{BASE_URL}/genai-assistant",
    "generate_quiz": f"{BASE_URL}/daacfa3e-4d93-4c26-8fd9-44d57c78c9bd",
    "quiz_feedback": f"{BASE_URL}/d01e73df-5c5b-44f8-ad15-0a46b8e039c1",
}

# ===== PAGE SETTINGS =====
st.set_page_config(
    page_title="GenAI Assistant for Education",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown(
    "<h1 style='text-align:center; color:#6A1B9A;'> GenAI Assistant for Education</h1>",
    unsafe_allow_html=True
)

# ===== Select Role =====
role = st.selectbox("Select your role:", ["Select...", "Teacher", "Student"])
if role == "Teacher":
    teacher_code = st.text_input("Enter teacher verification code:", type="password")

    if teacher_code != "GSU2025":  # <-- change this to your secret
        st.warning("Please enter a valid teacher verification code.")
        st.stop()

# -------------------------------------------------------------------------------------
#  TEACHER PANEL
# -------------------------------------------------------------------------------------
if role == "Teacher":
    st.markdown("## Teacher Dashboard")

    # Choose mode (ask question or summarize)
    mode = st.radio("Choose what you'd like to do:", ["Ask a question", "Summarize text"])

    # --- ASK QUESTION ---
    if mode == "Ask a question":
        st.subheader("")
        question = st.text_area("Your question:")
        if st.button("Get Answer"):
            if question.strip():
                payload = {
                    "role": "teacher",
                    "action": "question",
                    "question": question
                }
                try:
                    res = requests.post(WEBHOOKS["teacher"], json=payload)
                    res.raise_for_status()
                    output = res.json()

                    if isinstance(output, list) and len(output) > 0:
                        output = output[0]

                    if isinstance(output, dict):
                        st.success(output.get("output", str(output)))
                    else:
                        st.success(str(output))

                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter a question first.")

    # --- SUMMARIZE TEXT ---
    elif mode == "Summarize text":
        st.subheader("Paste or type text to summarize")
        user_text = st.text_area("Enter text to summarize (max ~2000 words):", height=300)
        if st.button("Summarize"):
            if user_text.strip():
                payload = {
                    "role": "teacher",
                    "action": "summarize",
                    "text": user_text
                }
                try:
                    res = requests.post(WEBHOOKS["teacher"], json=payload)
                    res.raise_for_status()
                    output = res.json()

                    if isinstance(output, list) and len(output) > 0:
                        output = output[0]

                    summary = output.get("output", str(output)) if isinstance(output, dict) else str(output)
                    st.success("Summary generated successfully!")
                    st.write(summary)

                except Exception as e:
                    st.error(f"Error summarizing text: {e}")
            else:
                st.warning("Please enter some text first.")

# -------------------------------------------------------------------------------------
#  STUDENT PANEL
# -------------------------------------------------------------------------------------
elif role == "Student":
    st.markdown("## Student Panel")
    student_mode = st.radio("Choose an option:", ["Book Chatbot", "Smart Quiz Mode"])

    # --- STUDENT CHATBOT ---
    if student_mode == "Book Chatbot":
        st.subheader("Ask about the book: *A Voyage to Arcturus*")
        user_q = st.text_input("Your question:")
        if st.button("Ask"):
            if user_q.strip():
                payload = {"role": "student", "action": "chatbot", "question": user_q}
                try:
                    res = requests.post(WEBHOOKS["teacher"], json=payload)
                    res.raise_for_status()
                    output = res.json()
                    if isinstance(output, list):
                        output = output[0]
                    st.info(output.get("output", str(output)))
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please type a question first.")

    # --- SMART QUIZ MODE ---
    elif student_mode == "Smart Quiz Mode":
        st.subheader("AI Quiz Generator with Instant Feedback")
        st.caption("Type a topic from the book and test your understanding instantly!")

        topic = st.text_input("Enter a topic or chapter:")
        if st.button("Generate Question"):
            st.session_state["feedback"] = ""
            st.session_state["student_answer"] = ""
            st.session_state["correct_answer"] = ""
            st.session_state["quiz_question"] = ""

            try:
                payload = {"role": "student", "action": "quiz", "topic": topic}
                res = requests.post(WEBHOOKS["generate_quiz"], json=payload)
                res_data = res.json()

                if "output" in res_data and isinstance(res_data["output"], str):
                    res_data = json.loads(res_data["output"])

                st.session_state["quiz_question"] = res_data.get("question", "No question returned.")
                st.session_state["correct_answer"] = res_data.get("answer", "")
                st.success("New question generated!")
            except Exception as e:
                st.error(f"Error generating question: {e}")

        if st.session_state.get("quiz_question"):
            st.write(f"**Question:** {st.session_state['quiz_question']}")
            answer = st.text_input("Your answer:", key="student_answer")

            if st.button("Submit Answer"):
                try:
                    payload = {
                        "role": "student",
                        "action": "quiz_feedback",
                        "question": st.session_state["quiz_question"],
                        "student_answer": answer,
                        "correct_answer": st.session_state["correct_answer"]
                    }

                    res = requests.post(WEBHOOKS["quiz_feedback"], json=payload)
                    feedback = res.json()

                    if "output" in feedback and isinstance(feedback["output"], str):
                        feedback = json.loads(feedback["output"])

                    is_correct = feedback.get("is_correct", False)
                    feedback_msg = feedback.get("feedback", "").strip()

                    if is_correct:
                        st.success(f"Correct! {feedback_msg or 'Excellent work!'}")
                    else:
                        st.error(f"Incorrect. {feedback_msg or 'Try reviewing this concept again.'}")
                except Exception as e:
                    st.error(f"Error evaluating answer: {e}")

            if st.button("New Question"):
                for key in ["quiz_question", "correct_answer", "student_answer", "feedback"]:
                    st.session_state.pop(key, None)
                st.rerun()


