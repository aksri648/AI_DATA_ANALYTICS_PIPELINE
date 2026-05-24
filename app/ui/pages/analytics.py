import streamlit as st
from app.services.analytics_service import analytics_service
from app.db.warehouse import warehouse
from app.utils.logging import logger


def render_analytics():
    st.markdown("## Conversational Analytics")
    st.markdown("Ask questions about your data in natural language.")

    col1, col2 = st.columns([3, 1])
    with col2:
        tables = warehouse.list_datasets()
        selected_table = st.selectbox("Active dataset", tables if tables else ["No data"], key="analytics_table")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "chart" in msg and msg["chart"]:
                st.components.v1.html(msg["chart"], height=400)
            if "insights" in msg:
                with st.expander("AI Analysis Details"):
                    st.markdown(msg["insights"])

    question = st.chat_input("Ask a question about your data...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    result = analytics_service.process_question(
                        question,
                        table_name=None if selected_table == "No data" else selected_table,
                    )

                    if result.get("requires_file"):
                        st.info(result.get("message", "Please upload data first."))
                        insight_text = result.get("message", "")
                    elif result.get("intent") == "sql":
                        if "error" in result:
                            insight_text = (
                                "**I could not run that SQL query.**\n\n"
                                f"{result['error']}"
                            )
                            st.markdown(insight_text)
                        else:
                            st.markdown("**Query Results:**")
                            st.dataframe(result.get("result", []), use_container_width=True)
                            insight_text = str(result.get("result", []))
                    elif result.get("intent") == "visualization":
                        st.markdown("**Generated Charts:**")
                        if result.get("chart"):
                            st.components.v1.html(result["chart"], height=450)
                        if result.get("kpis"):
                            cols = st.columns(len(result["kpis"]))
                            for i, kpi in enumerate(result["kpis"]):
                                cols[i].metric(kpi.get("title", ""), kpi.get("value", ""))
                        insight_text = "Charts generated"
                    elif result.get("intent") == "insights":
                        st.markdown("**AI Insights:**")
                        st.markdown(result.get("insights", ""))
                        insight_text = result.get("insights", "")
                    elif result.get("intent") == "report":
                        st.markdown("**Report generated.** Download from Reports page.")
                        insight_text = "Report generated"
                    else:
                        st.markdown(result.get("analysis", ""))
                        if result.get("chart"):
                            st.components.v1.html(result["chart"], height=400)
                        insight_text = result.get("analysis", "")

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": insight_text,
                        "chart": result.get("chart"),
                        "insights": result.get("insights", result.get("analysis", "")),
                    })

                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    logger.error(f"Analytics error: {e}")

    if st.session_state.chat_history and st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
