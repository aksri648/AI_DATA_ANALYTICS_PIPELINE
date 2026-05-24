import streamlit as st
from app.charts.dashboard_builder import dashboard_builder
from app.charts.chart_engine import chart_engine
from app.db.warehouse import warehouse


def render_dashboard():
    st.markdown("## Dashboards")
    st.markdown("Automatically generated analytics dashboards.")

    tables = warehouse.list_datasets()
    if not tables:
        st.info("No datasets available. Upload data first.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox("Select dataset", tables)
    with col2:
        dashboard_type = st.selectbox(
            "Dashboard type",
            ["auto", "sales", "finance", "hr", "marketing"],
        )

    if st.button("Generate Dashboard", type="primary", use_container_width=True):
        with st.spinner("Building dashboard..."):
            try:
                df = warehouse.get_dataset(selected)
                dashboard = dashboard_builder.auto_dashboard(df, dashboard_type)

                kpis = dashboard.get("kpis", [])
                if kpis:
                    st.subheader("Key Metrics")
                    cols = st.columns(len(kpis))
                    for i, kpi in enumerate(kpis):
                        delta = None
                        if kpi.get("trend") == "up":
                            delta = "+"  # noqa
                        elif kpi.get("trend") == "down":
                            delta = "-"  # noqa
                        cols[i].metric(
                            label=kpi.get("title", ""),
                            value=kpi.get("value", ""),
                            delta=delta,
                        )

                charts = dashboard.get("charts", {})
                if charts:
                    chart_items = list(charts.items())
                    for i in range(0, len(chart_items), 2):
                        row_cols = st.columns(2)
                        for j in range(2):
                            idx = i + j
                            if idx < len(chart_items):
                                name, fig = chart_items[idx]
                                if fig:
                                    with row_cols[j]:
                                        st.plotly_chart(fig, use_container_width=True)

                st.success("Dashboard generated successfully!")

            except Exception as e:
                st.error(f"Dashboard generation failed: {e}")

    with st.expander("Saved Dashboards"):
        st.info("Dashboard persistence coming soon.")
