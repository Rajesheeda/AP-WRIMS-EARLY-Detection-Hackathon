import re

with open("c:/AP-EarlyWarningSystem/app.py", "r", encoding="utf-8") as f:
    text = f.read()

# the body of tab_live
tab_live_content = """    with st.expander("📡 Live 2026 Data Stream"):
        st.info(f"Current: {score:.1f} vs Nov 18 peak: 86.4 CRITICAL")
        risk_banner(level, score, current_risk)
        l_col1, l_col2 = st.columns([2, 3])
        with l_col1:
            st.plotly_chart(make_gauge(score, level, "Live Risk Score"), width='stretch', key="chart_live_gauge_overview")
        with l_col2:
            st.subheader("Live Sensor Readings")
            show_metrics(current_data, current_risk)
            st.subheader("Factor Breakdown")
            st.plotly_chart(make_factor_chart(current_risk.get("top_factors", [])), width='stretch', key="chart_live_factors_overview")
        st.subheader("Live Map")
        m_live = make_map(current_risk, "Current")
        st_folium(m_live, use_container_width=True, height=420, returned_objects=[], key="map_live_overview")
"""

# Find end of tab_overview (line 765 where factors_overview is)
pattern_overview_end = r'(st\.plotly_chart\(make_factor_chart\(current_risk\.get\("top_factors", \[\]\)\), width=\'stretch\', key="factors_overview"\)\n)'
# Insert text right after it
text = re.sub(pattern_overview_end, r'\1\n' + tab_live_content + '\n', text)

# Delete tab_live definition entirely
pattern_live_delete = r'(# ---------------------------------------------------------------------------\n# Tab 3 — Live 2026\n# ---------------------------------------------------------------------------\ndef tab_live\(\):.*?(?=# ---------------------------------------------------------------------------\n# Tab 4 — How It Works))'
text = re.sub(pattern_live_delete, '', text, flags=re.DOTALL)

with open("c:/AP-EarlyWarningSystem/app.py", "w", encoding="utf-8") as f:
    f.write(text)

