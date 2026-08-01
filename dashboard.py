import streamlit as st
from agent import ask_agent
from sheet_tools import mark_status

st.set_page_config(page_title="Job Search Agent")
st.title("Job Search Agent")

# messages persist when script reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# renders a marked applied button under each unapplied job
def render_job_buttons(jobs, msg_index):
    for job in jobs:
        if job.get("status", "").lower() != "not applied":
            continue
        button_key = f"apply_{msg_index}_{job['id']}"
        if st.button(f"Mark Applied — {job['company']} ({job['title']})", key=button_key):
            result = mark_status(job["id"], "applied")
            if result.get("success"):
                job["status"] = "applied"
                st.rerun()
            else:
                st.error(f"Couldn't update status: {result.get('error')}")

# redisplay full conversation so far
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("jobs"):
            render_job_buttons(message["jobs"], i)

# chat-style text box
if user_input := st.chat_input("Ask about your saved jobs..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_agent(user_input)
        st.markdown(response["text"])
        render_job_buttons(response["jobs"], len(st.session_state.messages))

    st.session_state.messages.append({
        "role": "assistant",
        "content": response["text"],
        "jobs": response["jobs"],
    })