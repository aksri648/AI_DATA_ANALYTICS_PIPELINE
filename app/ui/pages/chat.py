import streamlit as st
from app.services.analytics_service import analytics_service
from app.db.warehouse import warehouse
from app.crew.crews.analytics_crew import AnalyticsCrew
from app.crew.memory.memory_manager import memory_manager


def render_chat():
    st.markdown("## Conversational Analytics Chat")
    st.markdown("Chat with your data using natural language.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("chart_html"):
                st.components.v1.html(msg["chart_html"], height=400)

    prompt = st.chat_input("Ask anything about your data...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Agents are analyzing..."):
                try:
                    tables = warehouse.list_datasets()
                    table_name = tables[-1] if tables else None

                    result = analytics_service.process_question(prompt, table_name)

                    if result.get("analysis"):
                        st.markdown(result["analysis"])
                        response_text = result["analysis"]
                    elif result.get("insights"):
                        st.markdown(result["insights"])
                        response_text = result["insights"]
                    elif result.get("message"):
                        st.info(result["message"])
                        response_text = result["message"]
                    else:
                        response_text = "Analysis complete."

                    if result.get("chart"):
                        st.components.v1.html(result["chart"], height=400)
                        chart = result["chart"]
                    else:
                        chart = None

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "chart_html": chart,
                    })

                    memory_manager.add_conversation("main", "user", prompt)
                    memory_manager.add_conversation("main", "assistant", response_text)

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})

    if st.button("Clear Chat"):
        st.session_state.messages = []
        memory_manager.reset()
        st.rerun()
