import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Review Workflow Dashboard", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f5f5f7;
}

.card {
    background: white;
    padding: 22px 24px;
    border-radius: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

.metric-val {
    font-size: 32px;
    font-weight: 600;
    color: #1d1d1f;
    line-height: 1.1;
}

.metric-label {
    color: #86868b;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 6px;
}

.metric-sub {
    color: #86868b;
    font-size: 12px;
    margin-top: 4px;
}

.section-title {
    font-size: 20px;
    font-weight: 600;
    color: #1d1d1f;
    margin-bottom: 4px;
}

.section-sub {
    font-size: 13px;
    color: #86868b;
    margin-bottom: 16px;
}

.tag {
    display: inline-block;
    background: #f0f0f5;
    color: #3a3a3c;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 9px;
    border-radius: 20px;
    margin-right: 4px;
    margin-top: 4px;
}

.tag.red { background: #fff1f0; color: #ff3b30; }
.tag.orange { background: #fff8f0; color: #ff9500; }
.tag.green { background: #f0fff4; color: #34c759; }
.tag.blue { background: #f0f4ff; color: #007aff; }

.support-bubble {
    background: linear-gradient(135deg, #007aff11, #5856d611);
    border: 1px solid #007aff22;
    border-radius: 14px;
    padding: 14px 18px;
    margin-top: 12px;
    font-size: 13px;
    color: #1d1d1f;
    line-height: 1.6;
}

.support-label {
    font-size: 11px;
    font-weight: 600;
    color: #007aff;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}

.before-card {
    background: #fff1f0;
    border: 1px solid #ff3b3022;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 10px;
    font-size: 13px;
    color: #3a3a3c;
    line-height: 1.7;
}

.after-card {
    background: #f0fff4;
    border: 1px solid #34c75922;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 10px;
    font-size: 13px;
    color: #3a3a3c;
    line-height: 1.7;
}

.context-box {
    background: #f5f5f7;
    border-radius: 12px;
    padding: 14px 16px;
    font-size: 13px;
    color: #3a3a3c;
    line-height: 1.7;
    margin-bottom: 16px;
}

.quote-box {
    border-left: 3px solid #007aff;
    padding: 10px 16px;
    background: #f0f4ff;
    border-radius: 0 12px 12px 0;
    font-size: 13px;
    color: #1d1d1f;
    font-style: italic;
    margin: 12px 0;
}
</style>
""", unsafe_allow_html=True)

if "classifier_result" not in st.session_state:
    st.session_state.classifier_result = None

PALETTE = ["#007aff", "#5856d6", "#ff9500", "#34c759", "#ff3b30", "#af52de", "#ff2d55"]
SEV_COLOR = {"minor": "#34c759", "moderate": "#ff9500", "major": "#ff3b30"}
TICK_FONT = dict(family="Inter", size=12, color="#3a3a3c")


@st.cache_data
def load_data():
    df = pd.read_excel("review_workflow_dataset_100.xlsx")
    df["ReviewRound"] = pd.to_numeric(df["ReviewRound"], errors="coerce")
    df["DaysToReturn"] = pd.to_numeric(df["DaysToReturn"], errors="coerce")
    df["Reopened"] = df["Reopened"].astype(str).str.lower().str.strip()
    return df


df = load_data()


def classify_comment(text):
    t = text.lower().strip()

    if any(w in t for w in ["regulation", "compliance", "gmp", "regulatory", "requirement", "21 cfr", "ich", "fda"]):
        return "compliance_concern", "major", "References regulatory language and likely needs clear resolution before approval."
    if any(w in t for w in ["cross-reference", "cross reference", "does not match", "mismatch", "linked", "referenced in"]):
        return "cross_reference_issue", "moderate", "Suggests a traceability or linkage gap across related records."
    if any(w in t for w in ["missing", "not included", "no mention", "absent", "omitted", "not found", "not present"]):
        return "missing_information", "moderate", "Indicates absent content or incomplete inclusion of required information."
    if any(w in t for w in ["inconsistent", "inconsistency", "contradicts", "conflict", "discrepancy", "disagrees"]):
        return "inconsistency", "moderate", "Suggests conflicting information that may require source clarification."
    if any(w in t for w in ["evidence", "supporting data", "attachment", "no data", "data not", "results not"]):
        return "evidence_gap", "moderate", "Points to missing or unclear evidence supporting the record."
    if any(w in t for w in ["section", "page", "refer to", "reference", "see also", "table", "figure"]):
        return "cross_reference_issue", "moderate", "May involve a section-link or internal reference issue."
    if any(w in t for w in ["format", "font", "spacing", "layout", "template", "alignment", "indentation"]):
        return "formatting", "minor", "Formatting-oriented feedback that may be separated from core content issues."
    if any(w in t for w in ["wording", "phrasing", "unclear", "ambiguous", "rewrite", "rephrase", "sentence", "grammar"]):
        return "wording", "minor", "Language-level feedback that may be treated as optional depending on context."

    return None, None, None


def base_layout(title):
    return dict(
        title=title,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=12),
        title_font=dict(family="Inter", size=14),
        margin=dict(t=50, b=80, l=40, r=20),
        xaxis=dict(
            type="category",
            tickangle=-30,
            tickfont=TICK_FONT,
            title_font=dict(family="Inter", size=12),
        ),
        yaxis=dict(
            tickfont=TICK_FONT,
            title_font=dict(family="Inter", size=12),
        ),
    )


def get_filtered_combo(dataframe, role, category, doctype):
    exact = dataframe[
        (dataframe["ReviewerRole"] == role)
        & (dataframe["CommentCategory"] == category)
        & (dataframe["DocType"] == doctype)
    ]
    if not exact.empty:
        return exact, "role + comment type + document type"

    role_cat = dataframe[
        (dataframe["ReviewerRole"] == role)
        & (dataframe["CommentCategory"] == category)
    ]
    if not role_cat.empty:
        return role_cat, "role + comment type"

    cat_only = dataframe[dataframe["CommentCategory"] == category]
    if not cat_only.empty:
        return cat_only, "comment type only"

    return dataframe.copy(), "overall dataset fallback"


st.markdown("## Review Workflow Dashboard")
st.markdown(
    '<p class="section-sub">Feedback consistency · Revision loops · Workflow visibility · Prototype</p>',
    unsafe_allow_html=True
)
st.markdown("""
<div class="context-box">
This prototype explores where review feedback becomes inconsistent, loop-heavy, or difficult to act on
within structured document workflows. Rather than automating reviewer judgment, it is designed to make
bottlenecks, comment patterns, and revision burden more visible.
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "🔥 Heatmap",
    "✅ Checklist",
    "📂 Document Journey",
    "↔️ Before / After",
    "🧪 Reviewer Simulation"
])

# ==========================
# TAB 1 — OVERVIEW
# ==========================
with tab1:
    total_docs = df["CaseID"].nunique()
    total_events = len(df)
    avg_round = df["ReviewRound"].mean()
    reopen_rate = (df["Reopened"] == "yes").mean() * 100
    avg_days = df["DaysToReturn"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, label, sub in [
        (c1, str(total_docs), "Documents", "unique cases"),
        (c2, str(total_events), "Review Events", "total interactions"),
        (c3, f"{avg_round:.1f}", "Avg Round", "per document"),
        (c4, f"{reopen_rate:.0f}%", "Reopen Rate", "of all events"),
        (c5, f"{avg_days:.1f}d", "Avg Turnaround", "days to return"),
    ]:
        with col:
            st.markdown(f"""
            <div class="card">
              <div class="metric-label">{label}</div>
              <div class="metric-val">{val}</div>
              <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    cat = df["CommentCategory"].value_counts().reset_index()
    cat.columns = ["Category", "Count"]

    fig1 = go.Figure()
    for i, row in cat.iterrows():
        fig1.add_trace(go.Bar(
            x=[str(row["Category"])],
            y=[row["Count"]],
            marker_color=PALETTE[i % len(PALETTE)],
            showlegend=False
        ))
    fig1.update_layout(**base_layout("Comment Category Distribution"), bargap=0.3)

    with col_a:
        st.plotly_chart(fig1, use_container_width=True)

    sev = df["Severity"].value_counts().reset_index()
    sev.columns = ["Severity", "Count"]
    fig2 = px.pie(
        sev,
        names="Severity",
        values="Count",
        title="Severity Breakdown",
        color="Severity",
        color_discrete_map=SEV_COLOR,
        hole=0.45
    )
    fig2.update_layout(
        paper_bgcolor="white",
        font=dict(family="Inter", size=12),
        title_font_size=14
    )

    with col_b:
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    turn = df.groupby("ReviewerRole", as_index=False)["DaysToReturn"].mean().round(1)
    fig3 = go.Figure()
    for i, row in turn.iterrows():
        fig3.add_trace(go.Bar(
            x=[str(row["ReviewerRole"])],
            y=[row["DaysToReturn"]],
            marker_color=PALETTE[i % len(PALETTE)],
            text=[row["DaysToReturn"]],
            textposition="outside",
            textfont=dict(family="Inter", size=12),
            showlegend=False
        ))
    fig3.update_layout(**base_layout("Avg Turnaround by Reviewer Role"), bargap=0.4)

    with col_c:
        st.plotly_chart(fig3, use_container_width=True)

    rd = df["ReviewRound"].value_counts().sort_index().reset_index()
    rd.columns = ["Round", "Count"]
    max_count = rd["Count"].max()

    fig4 = go.Figure()
    for _, row in rd.iterrows():
        intensity = row["Count"] / max_count
        r = 55
        g = int(138 + intensity * (55 - 138))
        b = int(255 + intensity * (200 - 255))
        color = f"rgba({r},{g},{b},1)"
        fig4.add_trace(go.Bar(
            x=[str(int(row["Round"]))],
            y=[row["Count"]],
            marker_color=color,
            showlegend=False
        ))
    fig4.update_layout(**base_layout("Review Round Distribution"), bargap=0.3)

    with col_d:
        st.plotly_chart(fig4, use_container_width=True)

# ==========================
# TAB 2 — HEATMAP
# ==========================
with tab2:
    st.markdown('<p class="section-title">Revision Bottleneck Heatmap</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-sub">Where delays accumulate across reviewer roles and document types</p>',
        unsafe_allow_html=True
    )

    h1, h2 = st.columns(2)

    pivot1 = df.pivot_table(
        values="DaysToReturn",
        index="ReviewerRole",
        columns="DocType",
        aggfunc="mean"
    ).round(1)

    fig_h1 = go.Figure(data=go.Heatmap(
        z=pivot1.values,
        x=pivot1.columns.tolist(),
        y=pivot1.index.tolist(),
        colorscale=[[0, "#e8f4ff"], [0.5, "#007aff"], [1, "#0040aa"]],
        text=pivot1.values,
        texttemplate="%{text}d",
        hovertemplate="Role: %{y}<br>DocType: %{x}<br>Avg Days: %{z}<extra></extra>"
    ))
    fig_h1.update_layout(
        title="Avg Turnaround: Reviewer × Doc Type",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", size=12),
        title_font_size=14,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig_h1.update_xaxes(tickfont=TICK_FONT)
    fig_h1.update_yaxes(tickfont=TICK_FONT)

    with h1:
        st.plotly_chart(fig_h1, use_container_width=True)

    pivot2 = df.pivot_table(
        values="EventID",
        index="ReviewerRole",
        columns="ReviewRound",
        aggfunc="count",
        fill_value=0
    )

    fig_h2 = go.Figure(data=go.Heatmap(
        z=pivot2.values,
        x=[f"Round {c}" for c in pivot2.columns.tolist()],
        y=pivot2.index.tolist(),
        colorscale=[[0, "#fff8f0"], [0.5, "#ff9500"], [1, "#c05000"]],
        text=pivot2.values,
        texttemplate="%{text}",
        hovertemplate="Role: %{y}<br>%{x}<br>Events: %{z}<extra></extra>"
    ))
    fig_h2.update_layout(
        title="Revision Loop Frequency: Reviewer × Round",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", size=12),
        title_font_size=14,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig_h2.update_xaxes(tickfont=TICK_FONT)
    fig_h2.update_yaxes(tickfont=TICK_FONT)

    with h2:
        st.plotly_chart(fig_h2, use_container_width=True)

    st.markdown("**High-friction zones** — top 10 slowest review events")
    top_slow = df.nlargest(10, "DaysToReturn")[
        ["CaseID", "DocType", "ReviewerRole", "ReviewRound", "CommentCategory", "Severity", "DaysToReturn", "Reopened"]
    ].reset_index(drop=True)
    st.dataframe(top_slow, use_container_width=True, hide_index=True)

# ==========================
# TAB 3 — CHECKLIST
# ==========================
with tab3:
    st.markdown('<p class="section-title">Review Checklist Assistant</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-sub">Standardize reviewer expectations · classify comment type · track friction patterns</p>',
        unsafe_allow_html=True
    )

    cl1, cl2 = st.columns([1, 1])

    with cl1:
        st.markdown("**📋 Pre-Review Checklist**")
        st.caption("Check off before submitting review comments")

        checklist_items = [
            ("critical", "Compliance requirements clearly referenced", "compliance_concern"),
            ("critical", "All regulatory citations verified and current", "compliance_concern"),
            ("moderate", "Cross-references checked for accuracy", "cross_reference_issue"),
            ("moderate", "Missing information flagged with specific location", "missing_information"),
            ("moderate", "Inconsistencies noted with original source cited", "inconsistency"),
            ("minor", "Wording suggestions marked as optional", "wording"),
            ("minor", "Formatting issues separated from content issues", "formatting"),
            ("minor", "Evidence gaps described with expected format", "evidence_gap"),
        ]

        checked = []
        for severity, item, category in checklist_items:
            col_check, col_text = st.columns([0.08, 0.92])

            with col_check:
                is_checked = st.checkbox("", key=f"chk_{item}")

            with col_text:
                color_class = {"critical": "red", "moderate": "orange", "minor": "green"}[severity]
                st.markdown(f"""
                <div style="padding:6px 0;">
                  <span style="font-size:13px;color:#1d1d1f;">{item}</span><br>
                  <span class="tag {color_class}">{severity}</span>
                  <span class="tag blue">{category.replace('_', ' ')}</span>
                </div>
                """, unsafe_allow_html=True)

            checked.append(is_checked)

        pct = int(sum(checked) / len(checklist_items) * 100)

        st.markdown(f"""
        <div style="margin-top:16px;padding:14px;background:#f5f5f7;border-radius:12px;">
          <div style="font-size:13px;color:#86868b;margin-bottom:6px;">Checklist completion</div>
          <div style="font-size:24px;font-weight:600;color:#1d1d1f;">{pct}%</div>
          <div style="background:#e5e5ea;border-radius:10px;height:6px;margin-top:8px;">
            <div style="background:#007aff;width:{pct}%;height:6px;border-radius:10px;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with cl2:
        st.markdown("**🧭 Comment-Type Classifier**")
        st.caption("Paste a comment · Ctrl+Enter or click to classify")

        with st.form(key="classifier_form"):
            comment_input = st.text_area(
                "comment",
                placeholder="e.g. 'The batch number in section 3.2 does not match the deviation record.'",
                height=120,
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Classify comment →", use_container_width=True)

        if submitted:
            if comment_input.strip():
                cat_r, sev_r, expl = classify_comment(comment_input)
                if cat_r is None:
                    st.session_state.classifier_result = {"error": True}
                else:
                    reopen_prob = df[df["CommentCategory"] == cat_r]["Reopened"].eq("yes").mean() * 100
                    similar = df[df["CommentCategory"] == cat_r][
                        ["CaseID", "DocType", "ReviewerRole", "CommentTextShort", "DaysToReturn"]
                    ].head(5).reset_index(drop=True)

                    st.session_state.classifier_result = {
                        "error": False,
                        "cat": cat_r,
                        "sev": sev_r,
                        "expl": expl,
                        "reopen": reopen_prob,
                        "similar": similar,
                    }
            else:
                st.warning("Please enter a review comment.")

        if st.session_state.classifier_result:
            r = st.session_state.classifier_result

            if r.get("error"):
                st.warning("Could not classify — try more specific terms such as 'missing', 'section', or 'compliance'.")
            else:
                sev_color = {"major": "red", "moderate": "orange", "minor": "green"}[r["sev"]]
                st.markdown(f"""
                <div class="support-bubble">
                  <div class="support-label">CLASSIFICATION RESULT</div>
                  <span class="tag blue">{r['cat'].replace('_', ' ')}</span>
                  <span class="tag {sev_color}">{r['sev']}</span>
                  <div style="margin-top:10px;font-size:13px;color:#3a3a3c;line-height:1.6;">{r['expl']}</div>
                  <div style="margin-top:12px;font-size:12px;color:#86868b;">
                    Historical reopen rate: <strong style="color:#ff9500;">{r['reopen']:.0f}%</strong>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Similar past comments**")
                st.dataframe(r["similar"], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**📊 Comment Category × Avg Turnaround**")
    st.caption("Which comment types are associated with longer delays?")

    friction = df.groupby("CommentCategory", as_index=False).agg(
        avg_days=("DaysToReturn", "mean"),
        reopen_rate=("Reopened", lambda x: (x == "yes").mean() * 100),
    ).round(1).sort_values("avg_days", ascending=False)

    fig_f = go.Figure()
    for _, row in friction.iterrows():
        intensity = row["reopen_rate"] / 100
        r_val = 255
        g_val = int(59 + (1 - intensity) * 150)
        fig_f.add_trace(go.Bar(
            x=[str(row["CommentCategory"])],
            y=[row["avg_days"]],
            marker_color=f"rgba({r_val},{g_val},48,0.85)",
            text=[row["avg_days"]],
            textposition="outside",
            textfont=dict(family="Inter", size=12),
            showlegend=False
        ))
    fig_f.update_layout(
        **base_layout("Avg Turnaround by Category (color intensity = reopen rate)"),
        bargap=0.3
    )
    st.plotly_chart(fig_f, use_container_width=True)

# ==========================
# TAB 4 — DOCUMENT JOURNEY
# ==========================
with tab4:
    st.markdown('<p class="section-title">Document Review Journey</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-sub">Trace the full review lifecycle of a single document</p>',
        unsafe_allow_html=True
    )

    selected_case = st.selectbox("Select a document", sorted(df["CaseID"].unique()), key="journey_selectbox")
    case_df = df[df["CaseID"] == selected_case].copy().sort_values("ReviewRound").reset_index(drop=True)

    doc_type = case_df["DocType"].iloc[0]
    total_rounds = int(case_df["ReviewRound"].max())
    total_days = int(case_df["DaysToReturn"].sum())
    reopened_count = int((case_df["Reopened"] == "yes").sum())

    m1, m2, m3, m4 = st.columns(4)
    for col, val, label in [
        (m1, doc_type, "Doc Type"),
        (m2, str(total_rounds), "Review Rounds"),
        (m3, f"{total_days}d", "Total Time"),
        (m4, str(reopened_count), "Reopened Events"),
    ]:
        with col:
            st.markdown(f"""
            <div class="card">
              <div class="metric-label">{label}</div>
              <div class="metric-val">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("**Review Timeline**")

    for _, row in case_df.iterrows():
        sev_colors = {"major": "#ff3b30", "moderate": "#ff9500", "minor": "#34c759"}
        color = sev_colors.get(str(row["Severity"]).lower(), "#86868b")
        reopen_badge = '<span class="tag red">reopened</span>' if str(row["Reopened"]).lower() == "yes" else ""
        sev_lower = str(row["Severity"]).lower()
        sev_class = "red" if sev_lower == "major" else "orange" if sev_lower == "moderate" else "green"

        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;margin-bottom:12px;">
          <div style="min-width:36px;height:36px;border-radius:50%;
                      background:{color}22;display:flex;align-items:center;
                      justify-content:center;font-size:12px;font-weight:600;
                      color:{color};margin-right:14px;margin-top:2px;">
            R{int(row['ReviewRound'])}
          </div>
          <div style="flex:1;background:#f5f5f7;border-radius:12px;padding:12px 14px;">
            <div style="font-size:13px;font-weight:500;color:#1d1d1f;margin-bottom:4px;">
              {row['ReviewerRole']} · {row['CommentTextShort']} {reopen_badge}
            </div>
            <div style="font-size:12px;color:#86868b;">
              <span class="tag">{str(row['CommentCategory']).replace('_', ' ')}</span>
              <span class="tag {sev_class}">{row['Severity']}</span>
              <span style="margin-left:8px;">⏱ {int(row['DaysToReturn'])}d to return</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    round_summary = case_df.groupby("ReviewRound", as_index=False).agg(
        events=("EventID", "count"),
        avg_days=("DaysToReturn", "mean"),
    ).round(1)

    fig_journey = make_subplots(specs=[[{"secondary_y": True}]])
    fig_journey.add_trace(
        go.Bar(
            x=round_summary["ReviewRound"].astype(str),
            y=round_summary["events"],
            name="Events",
            marker_color="#007aff",
            opacity=0.8
        ),
        secondary_y=False
    )
    fig_journey.add_trace(
        go.Scatter(
            x=round_summary["ReviewRound"].astype(str),
            y=round_summary["avg_days"],
            name="Avg Days",
            mode="lines+markers",
            line=dict(color="#ff9500", width=2),
            marker=dict(size=8)
        ),
        secondary_y=True
    )
    fig_journey.update_layout(
        title=f"Round-by-Round Summary · {selected_case}",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=12),
        title_font_size=14,
        legend=dict(orientation="h", y=1.1)
    )
    fig_journey.update_xaxes(type="category", tickfont=TICK_FONT)
    fig_journey.update_yaxes(tickfont=TICK_FONT, title_text="Events", secondary_y=False)
    fig_journey.update_yaxes(tickfont=TICK_FONT, title_text="Avg Days", secondary_y=True)

    st.plotly_chart(fig_journey, use_container_width=True)

# ==========================
# TAB 5 — BEFORE / AFTER
# ==========================
with tab5:
    st.markdown('<p class="section-title">Before / After · Workflow Support</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-sub">How workflow-support artifacts may change the review interaction experience</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="quote-box">In regulated environments, safety protocols protect the product — but not always the people maintaining them.</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="context-box">
    In pharmaceutical manufacturing, deviation and CAPA records are maintained within validated
    Word-based templates — meaning their structure cannot be casually redesigned without triggering
    re-validation. Workflow friction accumulates inside a system that is structurally rigid but
    socially variable: the format is fixed, yet the review experience depends heavily on reviewer
    style, comment habits, and interpretation differences.
    </div>
    """, unsafe_allow_html=True)

    ba_data = [
        ("Feedback consistency", "Reviewer-specific and variable", "Potentially more standardized through checklist scaffolds"),
        ("Revision burden", "Repeated loopbacks on small issues", "May be reduced through clearer distinctions between critical and optional feedback"),
        ("Workflow visibility", "Bottlenecks are difficult to localize", "Delay-heavy and loop-heavy stages become easier to observe"),
        ("Analyst confidence", "Often reactive and uncertain", "Could be supported through clearer review logic and expectations"),
        ("Compliance risk", "None", "None — support layer remains external to validated templates"),
    ]

    col_before, col_after = st.columns(2)

    with col_before:
        st.markdown("#### ❌ Before · No workflow support")
        for dim, before, _ in ba_data:
            st.markdown(f"""
            <div class="before-card">
              <strong style="font-size:11px;color:#ff3b30;text-transform:uppercase;letter-spacing:0.05em;">{dim}</strong><br>
              {before}
            </div>
            """, unsafe_allow_html=True)

    with col_after:
        st.markdown("#### ✅ After · With checklist + classifier")
        for dim, _, after in ba_data:
            st.markdown(f"""
            <div class="after-card">
              <strong style="font-size:11px;color:#34c759;text-transform:uppercase;letter-spacing:0.05em;">{dim}</strong><br>
              {after}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Observed Pain Points from Fieldwork**")

    pain_points = [
        (
            "Different reviewers applied different feedback standards and writing styles.",
            "Checklist scaffolds can help standardize expectations across reviewer roles."
        ),
        (
            "Batch numbers and deviation IDs had to be repeatedly copied across linked records.",
            "Workflow mapping can make cross-reference gaps more visible before review."
        ),
        (
            "Even small clarifications could trigger multi-day review loops.",
            "Comment-type classification can help distinguish optional wording edits from higher-stakes issues."
        ),
        (
            "Repeated revisions increased fatigue and reduced confidence.",
            "Visible revision patterns and bottleneck detection may reduce reactive work."
        ),
    ]

    for pain, fix in pain_points:
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f'<div class="before-card">⚠️ {pain}</div>', unsafe_allow_html=True)
        with p2:
            st.markdown(f'<div class="after-card">✅ {fix}</div>', unsafe_allow_html=True)

# ==========================
# TAB 6 — REVIEWER SIMULATION
# ==========================
with tab6:
    st.markdown('<p class="section-title">Reviewer Simulation Mode</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-sub">Explore how comment framing may relate to delay, reopening, and revision burden</p>',
        unsafe_allow_html=True
    )

    s1, s2 = st.columns([1.1, 0.9])

    with s1:
        with st.form(key="sim_form"):
            st.markdown("**Set the scene**")
            sim_doctype = st.selectbox("Document type", ["CAPA", "Deviation", "SOP", "ChangeControl"])
            sim_role = st.selectbox("Your reviewer role", ["QA", "QC", "RA"])
            sim_round = st.slider("Review round", 1, 5, 1)
            sim_comment = st.text_area(
                "Your review comment",
                placeholder="Write your comment as if you're reviewing a real document...",
                height=140,
                label_visibility="collapsed",
            )
            run_sim = st.form_submit_button("Run simulation →", use_container_width=True)

    with s2:
        st.markdown("**How this works**")
        st.markdown("""
        <div class="context-box">
        This simulation estimates the likely friction profile of a comment based on historical
        patterns in the prototype dataset — including reopen rates, turnaround times, and loop
        frequency by comment type, reviewer role, and document type where available.<br><br>
        It does not replace reviewer judgment. It is designed as a reflection aid that makes the
        possible consequences of comment framing more visible before feedback is submitted.
        </div>
        """, unsafe_allow_html=True)

        role_stats = df[df["ReviewerRole"] == sim_role].groupby("CommentCategory").agg(
            avg_days=("DaysToReturn", "mean"),
            reopen_rate=("Reopened", lambda x: (x == "yes").mean() * 100)
        ).round(1)

        st.markdown(f"**{sim_role} reviewer patterns**")
        st.dataframe(role_stats, use_container_width=True)

    if run_sim:
        if sim_comment.strip():
            cat_r, sev_r, expl = classify_comment(sim_comment)

            if cat_r is None:
                st.warning("Could not classify — try including more specific terms.")
            else:
                combo, basis = get_filtered_combo(df, sim_role, cat_r, sim_doctype)

                avg_days_role = combo["DaysToReturn"].mean()
                reopen_prob = combo["Reopened"].eq("yes").mean() * 100

                base_loop = reopen_prob
                round_penalty = (sim_round - 1) * 10
                doc_penalty = 5 if basis == "comment type only" else 0
                loop_risk = min(100, base_loop + round_penalty + doc_penalty)

                sev_color_hex = {
                    "major": "#ff3b30",
                    "moderate": "#ff9500",
                    "minor": "#34c759"
                }[sev_r]

                loop_color = "#ff3b30" if loop_risk > 60 else "#ff9500" if loop_risk > 30 else "#34c759"

                st.markdown("---")
                st.markdown("**Simulation Result**")

                r1, r2, r3, r4 = st.columns(4)
                for col, val, label, color in [
                    (r1, cat_r.replace("_", " "), "Comment Type", "#007aff"),
                    (r2, sev_r, "Severity", sev_color_hex),
                    (r3, f"{avg_days_role:.1f}d", "Expected Turnaround", "#5856d6"),
                    (r4, f"{loop_risk:.0f}%", "Loop Risk", loop_color),
                ]:
                    with col:
                        st.markdown(f"""
                        <div style="background:#f5f5f7;border-radius:12px;padding:14px 16px;text-align:center;">
                          <div style="font-size:12px;color:#86868b;margin-bottom:6px;">{label}</div>
                          <div style="font-size:20px;font-weight:600;color:{color};">{val}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="support-bubble" style="margin-top:16px;">
                  <div class="support-label">FRICTION ANALYSIS · {sim_role} · Round {sim_round} · {sim_doctype}</div>
                  {expl}<br><br>
                  <span style="color:#86868b;font-size:12px;">
                  Estimation basis: {basis}. Later review rounds are treated as more loop-sensitive because
                  unresolved earlier issues can amplify revision burden.
                  </span>
                </div>
                """, unsafe_allow_html=True)

                if sev_r == "minor":
                    rec = "💡 Consider marking this as optional feedback if it does not block clarity, traceability, or compliance."
                elif cat_r == "cross_reference_issue":
                    rec = "💡 Specify the exact section and expected reference format to reduce back-and-forth."
                elif cat_r == "missing_information":
                    rec = "💡 Include the exact missing field, its location, and expected format to make the comment easier to act on."
                else:
                    rec = "💡 Flag this clearly and anchor it to the relevant requirement or source record where possible."

                st.markdown(f"""
                <div style="background:#f0f4ff;border-radius:12px;padding:14px 16px;margin-top:12px;
                            font-size:13px;color:#1d1d1f;border:1px solid #007aff22;">
                  {rec}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("**How this comment type compares across all reviewers**")

                compare = df[df["CommentCategory"] == cat_r].groupby("ReviewerRole", as_index=False).agg(
                    avg_days=("DaysToReturn", "mean")
                ).round(1)

                fig_comp = go.Figure()
                for i, row in compare.iterrows():
                    fig_comp.add_trace(go.Bar(
                        x=[str(row["ReviewerRole"])],
                        y=[row["avg_days"]],
                        marker_color=PALETTE[i % len(PALETTE)],
                        text=[row["avg_days"]],
                        textposition="outside",
                        textfont=dict(family="Inter", size=12),
                        showlegend=False
                    ))
                fig_comp.update_layout(
                    **base_layout(f"Avg Turnaround for '{cat_r.replace('_', ' ')}' by Role"),
                    bargap=0.4
                )
                st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.warning("Please enter a review comment to run the simulation.")
