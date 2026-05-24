import streamlit as st
from app.crew.memory.memory_manager import memory_manager
from app.etl.pipeline_manager import etl_pipeline


def render_agent_monitor():
    st.markdown("## Agent Activity Monitor")
    st.markdown("Monitor CrewAI agent activities and workflow steps.")

    tab1, tab2, tab3 = st.tabs(["ETL Pipeline History", "Conversation Memory", "Workflow State"])

    with tab1:
        history = etl_pipeline.get_pipeline_history()
        if history:
            for h in reversed(history):
                with st.expander(f"**{h['step'].title()}** — `{h.get('table_name', '')}` ({h.get('timestamp', '')})"):
                    status = h.get("status", "unknown")
                    status_icon = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
                    st.markdown(f"**Status:** {status_icon} {status}")
                    st.json({k: v for k, v in h.items() if k not in ("id",)})
        else:
            st.info("No ETL pipeline history yet.")

    with tab2:
        conversations = memory_manager.get_conversation("main")
        if conversations:
            for msg in conversations[-30:]:
                role_icon = "🧑" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"]):
                    st.markdown(f"{role_icon} **{msg['role'].title()}** ({msg.get('timestamp', '')})")
                    st.text(msg["content"][:500])
        else:
            st.info("No conversation history yet.")

    with tab3:
        st.markdown("### Analytics Context")
        ctx = memory_manager.analytics_context
        if ctx:
            st.json(ctx)
        else:
            st.info("No analytics context stored yet.")

        st.markdown("### Schema Cache")
        cache = memory_manager.schema_cache
        if cache:
            for table, data in cache.items():
                st.markdown(f"- `{table}` (cached: {data.get('cached_at', '')})")
        else:
            st.info("No schema cache yet.")
