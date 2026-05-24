import streamlit as st
from app.charts.dashboard_builder import dashboard_builder
from app.charts.chart_engine import chart_engine
from app.db.warehouse import warehouse
from app.db.dashboard_store import dashboard_store


def _render_saved_dashboard(saved: dict):
    """Render a saved dashboard from its persisted HTML charts."""
    st.subheader(f"{saved['name']}")
    st.caption(f"Dataset: {saved['dataset_name']} | Type: {saved['dashboard_type']} | Updated: {saved['updated_at']}")

    kpis = saved.get("kpis", [])
    if kpis:
        st.markdown("### Key Metrics")
        cols = st.columns(min(len(kpis), 4))
        for i, kpi in enumerate(kpis):
            if i >= 4:
                break
            delta = None
            if kpi.get("trend") == "up":
                delta = "+"
            elif kpi.get("trend") == "down":
                delta = "-"
            cols[i].metric(
                label=kpi.get("title", ""),
                value=kpi.get("value", ""),
                delta=delta,
            )

    charts_html = saved.get("charts_html", {})
    if charts_html:
        st.markdown("### Charts")
        chart_items = list(charts_html.items())
        for i in range(0, len(chart_items), 2):
            row_cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(chart_items):
                    name, html = chart_items[idx]
                    if html:
                        with row_cols[j]:
                            st.components.v1.html(html, height=420, scrolling=True)


def render_dashboard():
    st.markdown("## Dashboards")
    st.markdown("Build, save, and load analytics dashboards.")

    tables = warehouse.list_datasets()
    saved_dashboards = dashboard_store.list_all()

    tab_build, tab_saved = st.tabs(["Build Dashboard", f"Saved Dashboards ({len(saved_dashboards)})"])

    # ── BUILD TAB ────────────────────────────────────────────────────
    with tab_build:
        if not tables:
            st.info("No datasets available. Upload data first.")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                selected = st.selectbox("Select dataset", tables, key="dash_dataset")
            with col2:
                dashboard_type = st.selectbox(
                    "Dashboard type",
                    ["auto", "sales", "finance", "hr", "marketing"],
                    key="dash_type",
                )

            if st.button("Generate Dashboard", type="primary", use_container_width=True, key="gen_dash"):
                with st.spinner("Building dashboard..."):
                    try:
                        df = warehouse.get_dataset(selected)
                        dashboard = dashboard_builder.auto_dashboard(df, dashboard_type)

                        kpis = dashboard.get("kpis", [])
                        if kpis:
                            st.subheader("Key Metrics")
                            cols = st.columns(min(len(kpis), 4))
                            for i, kpi in enumerate(kpis):
                                if i >= 4:
                                    break
                                delta = None
                                if kpi.get("trend") == "up":
                                    delta = "+"
                                elif kpi.get("trend") == "down":
                                    delta = "-"
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

                        st.session_state["last_dashboard"] = {
                            "kpis": kpis,
                            "charts_html": dashboard_builder.to_html_dict(dashboard),
                            "dashboard_type": dashboard_type,
                            "dataset_name": selected,
                        }
                        st.success("Dashboard generated successfully!")

                    except Exception as e:
                        st.error(f"Dashboard generation failed: {e}")

            # Save form (appears after a dashboard is generated)
            if "last_dashboard" in st.session_state:
                st.divider()
                st.markdown("#### Save Dashboard")
                with st.form("save_dashboard_form", clear_on_submit=True):
                    save_name = st.text_input("Dashboard name", placeholder="e.g. Q1 Sales Overview")
                    submitted = st.form_submit_button("Save", type="secondary", use_container_width=True)
                    if submitted:
                        if not save_name.strip():
                            st.error("Please enter a dashboard name.")
                        else:
                            last = st.session_state["last_dashboard"]
                            dashboard_store.save(
                                name=save_name.strip(),
                                dataset_name=last["dataset_name"],
                                dashboard_type=last["dashboard_type"],
                                kpis=last["kpis"],
                                charts_html=last["charts_html"],
                            )
                            st.success(f"Dashboard '{save_name.strip()}' saved!")
                            del st.session_state["last_dashboard"]
                            st.rerun()

    # ── SAVED TAB ────────────────────────────────────────────────────
    with tab_saved:
        if not saved_dashboards:
            st.info("No saved dashboards yet. Generate and save a dashboard from the Build tab.")
        else:
            for dash_meta in saved_dashboards:
                with st.expander(f"{dash_meta['name']}  —  {dash_meta['dataset_name']} ({dash_meta['dashboard_type']})", expanded=False):
                    col_view, col_del = st.columns([4, 1])
                    with col_view:
                        if st.button("Load", key=f"load_{dash_meta['id']}", use_container_width=True):
                            saved = dashboard_store.get_by_id(dash_meta["id"])
                            if saved:
                                st.session_state["view_dashboard"] = saved
                                st.rerun()
                    with col_del:
                        if st.button("Delete", key=f"del_{dash_meta['id']}", type="secondary", use_container_width=True):
                            dashboard_store.delete(dash_meta["id"])
                            st.success(f"Deleted '{dash_meta['name']}'")
                            st.rerun()

            # Render selected dashboard
            if "view_dashboard" in st.session_state:
                st.divider()
                _render_saved_dashboard(st.session_state["view_dashboard"])
                if st.button("Close", key="close_view"):
                    del st.session_state["view_dashboard"]
                    st.rerun()
