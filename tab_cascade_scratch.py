def tab_cascade():
    st.markdown("### 🌊 Cascade Network Intelligence — Pennar Basin")
    st.markdown("**Monitoring the entire upstream-downstream relationship network**")
    st.markdown("*Data source: APWRIMS live node data + risk engine*")
    
    btn_cols = st.columns(4)
    date_keys = ["Nov17", "Nov18", "Nov19", "Current"]
    if "cascade_date" not in st.session_state:
        st.session_state.cascade_date = "Nov17"
        
    for col, dk in zip(btn_cols, date_keys):
        risk = risks.get(dk, {})
        level = risk.get("level", "LOW")
        if col.button(f"📅 {DATE_LABELS.get(dk, 'Current')}\n**{level}**", width='stretch', key=f"btn_casc_{dk}"):
            st.session_state.cascade_date = dk
            
    dk = st.session_state.cascade_date
    data = all_data.get(dk, {})
    risk = risks.get(dk, {})
    level = risk.get("level", "LOW")
    score = risk.get("score", 0)

    # Coordinates
    pos = {
        "Pennar River": (5, 0),
        "Mylavaram": (5, 1),
        "Annamayya\\n(Under reconstruction)": (5, 2),
        "Cheyyeru River": (5, 3),
        "Pincha Project": (3, 4),
        "Bahuda River": (3, 5),
        "Gandikota": (7, 3),
        "Veligallu": (7, 4)
    }
    
    edges = [
        ("Bahuda River", "Pincha Project"),
        ("Pincha Project", "Cheyyeru River"),
        ("Cheyyeru River", "Annamayya\\n(Under reconstruction)"),
        ("Annamayya\\n(Under reconstruction)", "Mylavaram"),
        ("Mylavaram", "Pennar River"),
        ("Gandikota", "Pennar River"),
        ("Veligallu", "Pennar River")
    ]
    
    def get_color(node, selected_dk):
        if selected_dk == "Current":
            if "Pincha" in node: return "#D97706"
            if "Annamayya" in node: return "#DC2626"
            if "River" in node: return "#3B82F6"
            return "#94A3B8"
        elif selected_dk == "Nov18":
            if "Pincha" in node: return "#D97706"
            if "Annamayya" in node: return "#DC2626"
            if "Cheyyeru" in node: return "#EA580C"
            if "Gandikota" in node: return "#DC2626"
            if "River" in node: return "#3B82F6"
            return "#EA580C"
        elif selected_dk == "Nov19":
            if "Annamayya" in node: return "#000000"
            if "River" in node: return "#3B82F6"
            if "Pincha" in node: return "#DC2626"
            if "Cheyyeru" in node: return "#DC2626"
            return "#DC2626"
        else: # Nov17
            if "River" in node: return "#3B82F6"
            return "#16A34A"
            
    def get_hover(node, selected_dk):
        if "Annamayya" in node:
            return f"<b>{node}</b><br>Inflow: {data.get('annamayya_inflow',0)}<br>Outflow: {data.get('annamayya_outflow',0)}"
        elif "Pincha" in node:
            return f"<b>{node}</b><br>Inflow: {data.get('pincha_inflow',0)}<br>Outflow: {data.get('pincha_outflow',0)}"
        return f"<b>{node}</b>"
            
    edge_x, edge_y = [], []
    for u, v in edges:
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    node_x, node_y, node_colors, node_text, node_sizes = [], [], [], [], []
    for node, (x, y) in pos.items():
        node_x.append(x)
        node_y.append(y)
        node_colors.append(get_color(node, dk))
        size = 30
        if "Annamayya" in node: size = 45
        elif "Gandikota" in node: size = 50
        elif "Mylavaram" in node: size = 35
        elif "Pincha" in node: size = 25
        elif "Veligallu" in node: size = 25
        node_sizes.append(size)
        node_text.append(get_hover(node, dk))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, line=dict(width=2, color='#475569'), hoverinfo='none', mode='lines'
    ))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        text=[n.replace("\\n", "\n") for n in pos.keys()],
        textposition="bottom center",
        hoverinfo='text', hovertext=node_text,
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color='white'))
    ))
    fig.update_layout(
        plot_bgcolor='rgb(15, 23, 42)', paper_bgcolor='rgb(15, 23, 42)',
        font=dict(color='white'),
        showlegend=False,
        height=500,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    st.plotly_chart(fig, use_container_width=True, key="cascade_network_graph")

    # SECTION 4
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**Pincha Project**  \nStorage: 0.15 TMC (45.75%)  \nInflow: {data.get('pincha_inflow',0):,.0f} cs  \nOutflow: {data.get('pincha_outflow',0):,.0f} cs  \nRisk contribution: UPSTREAM TRIGGER")
    with c2:
        st.error(f"**Annamayya (Cheyyeru)**  \nStorage: {data.get('annamayya_storage_tmc', 0)} TMC  \nStatus: Under reconstruction  \nLast known: Nov 2021  \nRisk: MAXIMUM - structure offline")
    with c3:
        st.warning(f"**Cascade Status**  \nOverall network risk: {score}  \nActive alerts: {1 if level in ['HIGH','CRITICAL'] else 0}  \nCascade probability: {'High' if level in ['HIGH','CRITICAL'] else 'Low'}")

    # SECTION 6
    if dk == "Nov18":
        st.error("⚠️ CASCADE ALERT DETECTED\n\nPincha Project showing upstream stress (+16.6% inflow surge).\nAnnamayya receiving 11,531 cusecs with discharge exceeding inflow.\nGandikota releasing emergency 15,000 cusecs upstream.\nNetwork analysis indicates cascade failure probability: HIGH\nEstimated failure propagation time: 6-12 hours\nImmediate action required on nodes: Pincha, Annamayya")

    # SECTION 5
    if level in ["HIGH", "CRITICAL"]:
        st.markdown("---")
        tab_action_recommendations(dk)
