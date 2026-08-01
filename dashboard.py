import streamlit as st
from agent import ask_agent

st.set_page_config(page_title="Job Search Agent")
st.title("Job Search Agent")

# messages persist when script reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# redisplay full conversation so far
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# chat-style text box
if user_input := st.chat_input("Ask about your saved jobs..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_agent(user_input)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})