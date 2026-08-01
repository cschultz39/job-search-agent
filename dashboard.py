import streamlit as st
from agent import ask_agent
import pandas as pd
import altair as alt
from sheet_tools import mark_status, search_jobs, get_status_counts, get_status_history_weekly, STATUS_OPTIONS

st.set_page_config(page_title="Job Search Agent", layout="wide")

# custom CSS so page has no scrollbar
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 0rem;
        }
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Job Search Agent")

# page layout
left_col, right_col = st.columns([1, 2])

# information to cache in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "top_unapplied" not in st.session_state:
    st.session_state.top_unapplied = search_jobs(status="not applied", limit=10)

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

# metrics display
with right_col:
    st.subheader("Metrics")

    # status counts
    counts = get_status_counts()
    count_cols = st.columns(len(counts))
    for col, status in zip(count_cols, counts):
        col.metric(status, counts[status])

    # weekly status history chart
    st.markdown("**Status breakdown over time (weekly)**")
    weekly = get_status_history_weekly()
    if weekly:
        df = pd.DataFrame(weekly)
        long_df = df.melt(id_vars="week_of", var_name="status", value_name="count")
        chart = (
            alt.Chart(long_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("week_of:O", title="Week of"),
                y=alt.Y("count:Q", title="Job count"),
                color=alt.Color("status:N", title="Status", sort=STATUS_OPTIONS),
                tooltip=["week_of", "status", "count"],
            )
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.caption("No status changes logged yet — the chart fills in as you mark jobs applied/interviewing/etc.")

    # top 10 unapplied jobs
    st.markdown("**Top 10 unapplied jobs**")

    if not st.session_state.top_unapplied:
        st.caption("No unapplied jobs — nice, you're caught up!")
    else:
        for job in st.session_state.top_unapplied:
            job_col, btn_col = st.columns([5, 1])
            with job_col:
                st.markdown(
                    f"**{job['company']}** — {job['title']}  \n"
                    f"{job['location']} | score: {job.get('relevance_score', '?')}/10 | {job.get('relevance_reason', '')}  \n"
                    f"[Apply here]({job['link']})"
                )
            with btn_col:
                if st.button("Mark applied", key=f"top_apply_{job['id']}"):
                    result = mark_status(job["id"], "applied")
                    if result["success"]:
                        st.session_state.top_unapplied = search_jobs(status="not applied", limit=10)
                        st.rerun()
                    else:
                        st.error(result.get("error", "Failed to update status"))
            st.divider()

# chat display
with left_col:
    st.subheader("Chat")
    
    chat_container = st.container(height=380, border=False)
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("jobs"):
                    render_job_buttons(message["jobs"], i)

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