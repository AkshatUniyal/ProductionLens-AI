import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from engine import ReviewEngine
from database import Database
from analytics import Analytics
from exporter import Exporter
import json
import html
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="ProductionLens AI",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Init
db = Database()
engine = ReviewEngine()
analytics = Analytics(db)
exporter = Exporter()

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# State
if 'result' not in st.session_state:
    st.session_state.result = None
if 'active_example' not in st.session_state:
    st.session_state.active_example = None
if 'view_detail' not in st.session_state:
    st.session_state.view_detail = False
if "running_review" not in st.session_state:
    st.session_state.running_review = False
if "idea_input" not in st.session_state:
    st.session_state.idea_input = ""
if "widget_version" not in st.session_state:
    st.session_state.widget_version = 0

def h(value):
    return html.escape(str(value or ""), quote=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 1.5rem;">
        <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; letter-spacing: 0.1em; text-transform: uppercase;">Executive Hub</div>
    </div>
    """, unsafe_allow_html=True)
    
    stats = analytics.get_portfolio_stats()
    if stats:
        avg_score = int(stats['avg_readiness'])
        st.metric("Fleet Readiness", f"{avg_score}%", help="The average production-readiness score across all AI initiatives currently tracked in the portfolio.")
        st.markdown(f"""
        <div style="margin-top: -0.5rem; margin-bottom: 1.5rem;">
            <div style="height: 4px; background: #e2e8f0; border-radius: 2px;">
                <div style="height: 100%; width: {avg_score}%; background: #2563eb; border-radius: 2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    nav = st.radio("Navigation", ["Audit Engine", "Portfolio View", "Compare Reviews"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.7rem; color: #94a3b8; font-weight: 500;">
        SYSTEM STATUS: ONLINE<br>
        VERSION: 2.3.0 (Executive)
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;800&display=swap" rel="stylesheet">
<div class="top-header">
    <div class="top-header-left">
        <div class="logo-container">
            <svg width="44" height="44" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#93C5FD;stop-opacity:0.4" /><stop offset="100%" style="stop-color:#60A5FA;stop-opacity:0.6" /></linearGradient>
                    <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#60A5FA;stop-opacity:0.8" /><stop offset="100%" style="stop-color:#2563EB;stop-opacity:0.9" /></linearGradient>
                    <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#2563EB;stop-opacity:1" /><stop offset="100%" style="stop-color:#1D4ED8;stop-opacity:1" /></linearGradient>
                </defs>
                <path d="M24 6L42 15L24 24L6 15L24 6Z" fill="url(#grad1)" />
                <path d="M24 14L42 23L24 32L6 23L24 14Z" fill="url(#grad2)" />
                <path d="M24 22L42 31L24 40L6 31L24 22Z" fill="url(#grad3)" />
            </svg>
            <div class="logo-glow"></div>
        </div>
        <div style="margin-left: 0;">
            <div class="brand-name" style="font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 800; color: #1e293b;">ProductionLens <span style="color: #2563eb;">AI</span></div>
            <div class="brand-sub" style="font-family: 'Outfit', sans-serif; font-size: 0.75rem; color: #64748b; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;">ENTERPRISE READINESS ENGINE</div>
        </div>
    </div>
    <div class="status-pill">
        <div class="pulse-dot"></div>
        <span>SECURED LOCAL MODE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ROUTER
if nav == "Audit Engine":
    if st.session_state.result is None:
        # SCREEN 1: INPUT
        hero_col, hiw_col = st.columns([2, 1], gap="large")
        with hero_col:
            st.markdown("""<div class="hero-title">Evaluate whether an AI idea<br>is ready for production</div><div class="hero-subtitle">Review AI initiatives through architecture, data, RAG, security, and executive lenses.</div>""", unsafe_allow_html=True)
            with st.expander("ℹ️ How this Engine works (Demo Reference Guide)"):
                st.markdown("""
                <div style="padding: 1.25rem; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 2rem;">
                        <div>
                            <div style="font-weight: 700; color: #1e293b; margin-bottom: 0.75rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Review Modes</div>
                            <ul style="font-size: 0.8rem; color: #64748b; padding-left: 1.2rem; line-height: 1.6;">
                                <li><b>Full Review:</b> Deep dive into all 8 technical & business lenses.</li>
                                <li><b>Executive:</b> Focus on ROI & strategic alignment.</li>
                                <li><b>RAG Readiness:</b> Data quality & retrieval specific.</li>
                            </ul>
                        </div>
                        <div>
                            <div style="font-weight: 700; color: #1e293b; margin-bottom: 0.75rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Engine Outputs</div>
                            <ul style="font-size: 0.8rem; color: #64748b; padding-left: 1.2rem; line-height: 1.6;">
                                <li><b>Pilot Plan:</b> 3-month validation roadmap.</li>
                                <li><b>Gap Map:</b> Critical delta for production readiness.</li>
                                <li><b>Checklist:</b> Risk mitigation task list.</li>
                            </ul>
                        </div>
                        <div>
                            <div style="font-weight: 700; color: #1e293b; margin-bottom: 0.75rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Project Stack</div>
                            <ul style="font-size: 0.8rem; color: #64748b; padding-left: 1.2rem; line-height: 1.6;">
                                <li><b>LLM:</b> Llama 3.2 (Local via Ollama)</li>
                                <li><b>UI:</b> Streamlit (Enterprise Framework)</li>
                                <li><b>Persistence:</b> Local SQLite Database</li>
                                <li><b>Security:</b> 100% On-Premise Execution</li>
                            </ul>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        with hiw_col:
            st.markdown("""<div class="hiw-card"><div class="hiw-title">How it works</div><div class="hiw-step"><div class="hiw-num">1</div><div class="hiw-text">Submit AI idea</div></div><div class="hiw-step"><div class="hiw-num">2</div><div class="hiw-text">Run multi-lens review</div></div><div class="hiw-step"><div class="hiw-num">3</div><div class="hiw-text">Get score & next steps</div></div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="input-header" style="margin-top: 2rem;"><div class="input-card-title">Review Input</div></div>', unsafe_allow_html=True)
        
        def set_idea(text, name):
            st.session_state.idea_input = text
            st.session_state.project_name = name
            st.session_state.active_example = name
            st.session_state.widget_version += 1

        if "project_name" not in st.session_state:
            st.session_state.project_name = ""

        widget_key = f"idea_input_v{st.session_state.widget_version}"
        
        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;'>Project Name</p>", unsafe_allow_html=True)
        proj_name = st.text_input("Project Name", value=st.session_state.project_name, key=f"proj_name_{st.session_state.widget_version}", label_visibility="collapsed", placeholder="e.g. Market Intelligence Tool")
        if proj_name != st.session_state.project_name:
            st.session_state.project_name = proj_name

        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem; margin-top: 1rem;'>Project Description</p>", unsafe_allow_html=True)
        idea_text = st.text_area("Project description", value=st.session_state.idea_input, height=140, key=widget_key, label_visibility="collapsed")
        if idea_text != st.session_state.idea_input:
            st.session_state.idea_input = idea_text

        st.markdown('<p style="font-size: 0.85rem; color: #64748b; margin-top: 1rem;">Example inputs</p>', unsafe_allow_html=True)
        examples = {
            "Sales Platform AI": "A highly secure, on-premise AI model with RBAC, but using messy, unoptimized raw SQL data and no RAG pipeline.",
            "Market Intel Tool": "A state-of-the-art vector DB and advanced RAG pipeline for market data, but hosted on public cloud with zero encryption or security logging.",
            "Agentic Support": "We want to build an AI agent that autonomously handles customer support tickets and retrieving order data.",
            "HR Policy Bot": "We are building an HR assistant that answers policy questions based on company handbooks.",
            "Content Automator": "AI automatically creates customer decks based on product recommendations and sends them to prospects.",
            "Market Engine": "Tool that analyzes market trends and competitor data to recommend pricing strategies."
        }
        
        pill_cols = st.columns(6)
        for i, (label, text) in enumerate(examples.items()):
            with pill_cols[i]:
                btn_type = "primary" if st.session_state.active_example == label else "secondary"
                if st.button(label, use_container_width=True, type=btn_type):
                    set_idea(text, label)
                    st.rerun()

        ctrl_cols = st.columns([1.5, 1.5, 1, 1, 2], vertical_alignment="center")
        mode = ctrl_cols[0].selectbox("Review Mode", ["Full Production Review", "Executive Review", "RAG Readiness", "Architecture Review"])
        depth = ctrl_cols[1].selectbox("Response Depth", ["Standard", "Deep Dive", "Concise"])
        with ctrl_cols[2]: st.toggle("Pilot Plan", value=True, key="pilot_toggle")
        with ctrl_cols[3]: st.toggle("Checklist", value=True, key="check_toggle")
        
        btn_label = "⌛ Running Review..." if st.session_state.running_review else "▶ Run Review"
        if ctrl_cols[4].button(btn_label, type="primary", use_container_width=True, disabled=st.session_state.running_review):
            st.session_state.running_review = True
            st.rerun()

        if st.session_state.running_review:
            with st.spinner("Processing..."):
                try:
                    result = engine.get_review(st.session_state.idea_input, mode, depth, include_pilot=st.session_state.pilot_toggle, include_checklist=st.session_state.check_toggle)
                    res_dict = result.model_dump()
                    if st.session_state.project_name:
                        res_dict['project_name'] = st.session_state.project_name
                    st.session_state.result = res_dict
                    db.save_review(st.session_state.idea_input, mode, depth, result)
                except Exception as e: st.error(f"Error: {e}")
                finally:
                    st.session_state.running_review = False
                    st.rerun()

    else:
        # SCREEN 2: RESULTS
        res = st.session_state.result
        if st.button("← Back to Input"):
            st.session_state.result = None
            st.rerun()

        st.markdown("## Review Results")
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            score = res['readiness_score']
            st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Readiness Score</div><div style="display: flex; align-items: center; gap: 1rem;"><svg width="80" height="80" viewBox="0 0 80 80"><circle cx="40" cy="40" r="35" fill="none" stroke="#e2e8f0" stroke-width="6"/><circle cx="40" cy="40" r="35" fill="none" stroke="#2563eb" stroke-width="6" stroke-dasharray="{score * 2.2} 220" transform="rotate(-90 40 40)"/><text x="40" y="45" text-anchor="middle" font-size="18" font-weight="800" fill="#1e293b">{score}</text></svg><div><div style="font-size: 0.85rem; font-weight: 700;">{h(res.get('score_tagline', 'Audit Complete'))}</div></div></div></div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Recommendation</div><div style="font-size: 1.1rem; font-weight: 800; color: #2563eb;">{h(res['recommendation'])}</div><div style="font-size: 0.75rem; color: #64748b;">{h(res.get('recommendation_tagline', ''))}</div></div>""", unsafe_allow_html=True)
        with m3:
            roi = res.get('roi_score', 5)
            st.markdown(f"""<div class="metric-card"><div class="metric-card-label">ROI Potential</div><div style="font-size: 1.5rem; font-weight: 800; color: #7c3aed;">{roi}/10</div><div style="height: 4px; background: #e2e8f0; margin-top: 0.5rem;"><div style="height: 100%; width: {roi*10}%; background: #7c3aed; border-radius: 2px;"></div></div></div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Est. Pilot Budget</div><div style="font-size: 1.5rem; font-weight: 800; color: #0891b2;">{h(res.get('estimated_pilot_cost', 'TBD'))}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="section-card"><div class="section-title">Executive Summary</div><div style="font-size: 0.95rem; line-height: 1.6; color: #334155;">{h(res['executive_summary'])}</div></div>""", unsafe_allow_html=True)

        st.markdown("### Lens Breakdown")
        lens_cols = st.columns(4)
        for i, lens in enumerate(res['lens_scores']):
            with lens_cols[i % 4]:
                # UI FIX: Added margin-bottom so multiple rows of cards have vertical breathing space.
                st.markdown(f"""<div class="lens-card" style="display: flex; flex-direction: column; justify-content: flex-start; min-height: 135px; padding: 1.25rem; margin-bottom: 1.25rem;"><div style="display: flex; justify-content: space-between; width: 100%; align-items: baseline; margin-bottom: 0.75rem;"><div class="lens-name" style="font-size: 0.85rem; font-weight: 700; color: #1e293b;">{h(lens['lens'])}</div><div class="lens-score" style="color: #2563eb; font-weight: 800; font-size: 0.95rem; margin-left: 10px;">{lens['score']}/10</div></div><div class="lens-rationale" style="font-size: 0.75rem; line-height: 1.5; color: #64748b;">{h(lens['rationale'])}</div></div>""", unsafe_allow_html=True)

        if st.session_state.get("check_toggle", True):
            rows = "".join([f'<tr><td><span class="pilot-check">✓</span></td><td><b>{h(r["risk"])}</b></td><td>{h(r["mitigation"])}</td></tr>' for r in res['risks'][:5]])
            st.markdown(f"""<div class="section-card"><div class="section-title">✅ Readiness Checklist</div><table class="risk-table"><tr><th></th><th>Task</th><th>Mitigation</th></tr>{rows}</table></div>""", unsafe_allow_html=True)

        col_left, col_right = st.columns([2, 1])
        with col_left:
            if st.session_state.get("pilot_toggle", True):
                # UI FIX: Enhanced Pilot Plan with a timeline-style grid and "Stage" indicators
                items = ""
                for idx, item in enumerate(res.get('pilot_plan', [])):
                    items += f'<div style="padding: 1rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; position: relative;"><div style="font-size: 0.65rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.5rem;">Phase {idx+1}</div><div style="font-size: 0.85rem; font-weight: 600; color: #1e293b; display: flex; align-items: center; gap: 8px;"><span class="pilot-check">✓</span> {h(item)}</div></div>'
                
                st.markdown(f"""<div class="section-card" style="height: 100%;"><div class="section-title">🚀 Pilot Plan: {h(res['suggested_next_step'])}</div><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">{items}</div></div>""", unsafe_allow_html=True)
        with col_right:
            # UI FIX: Removed 'height: 100%' so the Gap Map shrinks to wrap its content and avoids giant empty dead spaces.
            gaps = "".join([f'<div style="padding: 1rem; border-bottom: 1px solid #f1f5f9; background: #ffffff;"><div style="font-size: 0.85rem; font-weight: 700; color: #1e293b; margin-bottom: 0.25rem;">{h(g["feature"])}</div><div style="font-size: 0.75rem; color: #64748b; line-height: 1.4;"><span style="color: #64748b;">Current:</span> {h(g["in_demo"])}<br><span style="color: #2563eb; font-weight: 600;">Required:</span> {h(g["in_production"])}</div></div>' for g in res.get('gaps', [])])
            st.markdown(f"""<div class="sidebar-card" style="padding: 0;"><div class="sidebar-title" style="padding: 1.25rem 1.25rem 0.75rem 1.25rem;">⚡ Gap Map</div>{gaps}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        pdf_bytes = exporter.generate_pdf(res)
        st.download_button(label="Download PDF Report", data=bytes(pdf_bytes), file_name="ProductionLens_Report.pdf", mime="application/pdf", type="primary", use_container_width=True)

elif nav == "Portfolio View":
    st.markdown("## 📊 Portfolio Intelligence")
    stats = analytics.get_portfolio_stats()
    if stats:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Audits", stats['total_reviews'])
        c2.metric("Avg Readiness", f"{int(stats['avg_readiness'])}%")
        c3.metric("Avg ROI", f"{stats['avg_roi']:.1f}/10")
        st.markdown("---")
        st.markdown("### Readiness Score Trend: Organization Maturity Journey")
        st.line_chart(stats['maturity_trend'].set_index('Date'))
        
        st.markdown("---")
        st.markdown("### 📋 Fleet Roster: Active Audits")
        
        # Display the roster as a clean, styled table
        roster_df = pd.DataFrame(stats['roster'])
        if not roster_df.empty:
            # Create a more visual table representation
            for item in stats['roster']:
                with st.container():
                    col_t, col_s, col_st = st.columns([4, 1, 1])
                    col_t.markdown(f"**{item['title']}**")
                    col_s.markdown(f"**{item['score']}%**")
                    col_st.markdown(f'<span style="color: {item["color"]}; font-weight: 800; font-size: 0.8rem; text-transform: uppercase;">● {item["status"]}</span>', unsafe_allow_html=True)
                    st.markdown('<div style="height: 1px; background: #f1f5f9; margin-bottom: 0.5rem;"></div>', unsafe_allow_html=True)

elif nav == "Compare Reviews":
    st.markdown("## ⚖️ Comparative Analysis")
    history = db.get_history()
    if len(history) >= 2:
        # HUMAN-READABLE SELECTORS
        opts = {}
        fallback_names = ["Sales Intelligence AI", "Customer Support Bot", "Market Analytics", "HR Assistant"]
        for h in history:
            try:
                res_obj = json.loads(h['result_json'])
                title = res_obj.get('project_name') or fallback_names[h['id'] % len(fallback_names)]
                label = f"{title} ({h['timestamp'][:10]})"
                opts[label] = h['id']
            except:
                label = f"Review {h['id']} ({h['timestamp'][:10]})"
                opts[label] = h['id']
        
        id1 = st.selectbox("Baseline Review (Current State)", list(opts.keys()))
        id2 = st.selectbox("Comparison Review (Target/Alternative)", list(opts.keys()))
        
        if st.button("Generate Comparative Benchmark", type="primary"):
            comp = analytics.get_comparison(opts[id1], opts[id2])
            
            # EXTRACT SCORES
            l_scores = {l['lens']: l['score'] for l in comp['left']['lens_scores']}
            r_scores = {l['lens']: l['score'] for l in comp['right']['lens_scores']}
            categories = list(l_scores.keys())

            # TITLE & DELTA
            fallback_names = ["Sales Intelligence AI", "Customer Support Bot", "Market Analytics", "HR Assistant"]
            l_name = comp['left'].get('project_name') or fallback_names[opts[id1] % len(fallback_names)]
            r_name = comp['right'].get('project_name') or fallback_names[opts[id2] % len(fallback_names)]
            st.markdown(f"### Benchmark: {l_name} vs. {r_name}")
            
            # Compute actual gap from lens scores to prevent 0% ties on different profiles
            l_avg = sum(l_scores.values()) / len(l_scores) * 10
            r_avg = sum(r_scores.values()) / len(r_scores) * 10
            diff = round(r_avg - l_avg, 1)
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Readiness Performance Gap", f"{round(r_avg)}%", f"{diff}%")
            
            st.markdown("---")
            
            # RADAR CHART
            st.markdown("#### 🕸️ Technical Readiness Footprint")
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=[l_scores.get(c, 0) for c in categories], theta=categories, fill='toself', name=l_name, line_color='#2563eb'))
            fig.add_trace(go.Scatterpolar(r=[r_scores.get(c, 0) for c in categories], theta=categories, fill='toself', name=r_name, line_color='#7c3aed'))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                showlegend=True,
                margin=dict(l=40, r=40, t=20, b=20),
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)

            # STRATEGIC INSIGHT
            st.markdown("#### 💡 Strategic Consultant Insight")
            l_ex = comp['left'].get('executive_summary', '')
            r_ex = comp['right'].get('executive_summary', '')
            
            # Generate a "Consultant-style" specific contrast based on relative DELTAS, not absolute maximums
            deltas = {lens: r_scores.get(lens, 0) - l_scores.get(lens, 0) for lens in categories}
            best_l_lens = min(deltas, key=deltas.get) # Where Left beats Right the most
            best_r_lens = max(deltas, key=deltas.get) # Where Right beats Left the most
            
            l_win = l_scores.get(best_l_lens, 0)
            r_win = r_scores.get(best_r_lens, 0)
            
            if deltas[best_l_lens] < 0 and deltas[best_r_lens] > 0:
                insight_text = f"<b>Comparative Analysis:</b> While <b>{h(l_name)}</b> outperforms in <i>{h(best_l_lens)}</i> ({l_win}/10 vs {r_scores.get(best_l_lens, 0)}/10), <b>{h(r_name)}</b> demonstrates superior performance in <i>{h(best_r_lens)}</i> ({r_win}/10 vs {l_scores.get(best_r_lens, 0)}/10). "
            elif deltas[best_l_lens] < 0:
                insight_text = f"<b>Comparative Analysis:</b> <b>{h(l_name)}</b> dominates across all metrics, notably outperforming in <i>{h(best_l_lens)}</i> ({l_win}/10 vs {r_scores.get(best_l_lens, 0)}/10). "
            elif deltas[best_r_lens] > 0:
                insight_text = f"<b>Comparative Analysis:</b> <b>{h(r_name)}</b> dominates across all metrics, notably outperforming in <i>{h(best_r_lens)}</i> ({r_win}/10 vs {l_scores.get(best_r_lens, 0)}/10). "
            else:
                insight_text = f"<b>Comparative Analysis:</b> Both projects show exact technical parity across all 8 lenses. "

            if diff > 0:
                insight_text += f"The <b>{diff}% readiness advantage</b> in {h(r_name)} is primarily driven by its more robust architectural framework."
            elif diff < 0:
                insight_text += f"<b>{h(l_name)}</b> maintains a technical lead of <b>{abs(diff)}%</b> due to its superior security and data posture."
            else:
                if deltas[best_l_lens] < 0 and deltas[best_r_lens] > 0:
                    insight_text += f"<b>{h(l_name)}</b> holds a technical edge in {h(best_l_lens)}; <b>{h(r_name)}</b> has a stronger {h(best_r_lens)} posture — fund based on which risk you're willing to carry."
                else:
                    insight_text += "Both projects show technical parity; selection should be based on immediate business ROI rather than architectural readiness."
            
            st.markdown(f'<div class="section-card" style="background: #eff6ff; border-left: 4px solid #2563eb; font-size: 0.95rem; color: #1e3a8a;">{insight_text}</div>', unsafe_allow_html=True)

            st.markdown("#### 8-Lens Performance Benchmark")
            
            # CREATE COMPARISON TABLE
            rows = ""
            for lens in categories:
                s1 = l_scores.get(lens, 0)
                s2 = r_scores.get(lens, 0)
                delta = s2 - s1
                delta_color = "#10b981" if delta > 0 else "#ef4444" if delta < 0 else "#64748b"
                delta_sign = "+" if delta > 0 else ""
                
                rows += f'<tr><td style="padding: 12px; font-weight: 700; color: #1e293b;">{h(lens)}</td>'
                rows += f'<td style="padding: 12px; text-align: center;">{s1}/10</td>'
                rows += f'<td style="padding: 12px; text-align: center; font-weight: 800;">{s2}/10</td>'
                rows += f'<td style="padding: 12px; text-align: center; color: {delta_color}; font-weight: 800;">{delta_sign}{delta}</td></tr>'
            
            table_html = f"""
            <div class="section-card" style="padding: 0; overflow: hidden;">
                <table style="width: 100%; border-collapse: collapse; background: white;">
                    <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                        <th style="padding: 12px; text-align: left; font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Lens Dimension</th>
                        <th style="padding: 12px; text-align: center; font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Baseline</th>
                        <th style="padding: 12px; text-align: center; font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Comparison</th>
                        <th style="padding: 12px; text-align: center; font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Delta</th>
                    </tr>
                    {rows}
                </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)
            
            st.markdown("---")
            col_l, col_r = st.columns(2)
            col_l.markdown(f"#### Baseline Recommendation\n{comp['left']['recommendation']}: {comp['left'].get('recommendation_tagline', '')}")
            col_r.markdown(f"#### Comparison Recommendation\n{comp['right']['recommendation']}: {comp['right'].get('recommendation_tagline', '')}")
