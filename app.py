import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Loyalty Engine Calculator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Space Mono', monospace !important;
}

.stApp {
    background-color: #0e0f14;
    color: #e8e9f0;
}

section[data-testid="stSidebar"] {
    background-color: #13141c;
    border-right: 1px solid #1f2030;
}

section[data-testid="stSidebar"] h2 {
    color: #7ee8a2;
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 1.5rem;
}

.metric-card {
    background: #13141c;
    border: 1px solid #1f2030;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.5rem;
}

.metric-card .label {
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6b7280;
    font-family: 'Space Mono', monospace;
}

.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    color: #7ee8a2;
    line-height: 1.1;
    margin-top: 0.2rem;
}

.metric-card .sub {
    font-size: 0.78rem;
    color: #4b5563;
    margin-top: 0.3rem;
}

.tier-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.3rem 0.7rem;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 0.8rem;
}

.tier-power  { background: #2d1f4e; color: #c084fc; }
.tier-mid    { background: #1a2d3d; color: #60c8f5; }
.tier-casual { background: #1a2d1f; color: #7ee8a2; }

.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4b5563;
    border-bottom: 1px solid #1f2030;
    padding-bottom: 0.5rem;
    margin: 1.2rem 0 0.8rem 0;
}

.stSlider > div > div > div > div {
    background: #7ee8a2 !important;
}

.highlight-box {
    background: linear-gradient(135deg, #13141c, #1a1f2e);
    border: 1px solid #2d3748;
    border-left: 3px solid #7ee8a2;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    font-size: 0.88rem;
    color: #9ca3af;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: #13141c;
    border-bottom: 1px solid #1f2030;
    gap: 0;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4b5563;
    padding: 0.8rem 1.5rem;
    border: none;
    background: transparent;
}

.stTabs [aria-selected="true"] {
    color: #7ee8a2 !important;
    border-bottom: 2px solid #7ee8a2 !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar: All Parameters ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# ⚙️ Loyalty Engine")
    st.markdown("---")

    # ── Earn & Withdrawal Caps ──
    st.markdown("## Reward Caps")
    monthly_earn_cap = st.number_input("Max monthly earn cap (USD)", min_value=50, max_value=500, value=100, step=10)
    monthly_withdraw_cap = st.number_input("Min monthly withdrawal cap (USD)", min_value=1, max_value=500, value=20, step=10)

    # ── Budget Allocation ──
    st.markdown("## Reward Structure")
    pct_reviews  = st.slider("% of earn cap → Reviews",  0, 100, 80, 1)
    pct_forum    = st.slider("% of earn cap → Forum",    0, 100, 15, 1)
    pct_login    = st.slider("% of earn cap → Logins",   0, 100, 5,  1)

    alloc_sum = pct_reviews + pct_forum + pct_login
    if alloc_sum != 100:
        st.warning(f"Reward structure sums to {alloc_sum}% (should be 100%)")

    # ── Reward Unit Values ──
    st.markdown("## Rewards")
    earn_per_review = st.number_input("Earn per confirmed review (USD)",      min_value=1,   max_value=10,   value=8,   step=1)
    earn_per_post   = st.number_input("Earn per qualifying forum post (USD)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
    earn_per_login  = st.number_input("Earn per weekly login reward (USD)",   min_value=0.1, max_value=20.0, value=1.0, step=0.1)

    # ── Qualification Rules ──
    st.markdown("## Qualification Rules")
    likes_to_qualify = st.number_input("Likes needed per forum post to qualify", min_value=0, max_value=50, value=5, step=1)
    logins_per_week  = st.number_input("Logins/week to qualify for login reward", min_value=1, max_value=7, value=3, step=1)

    # ── User Base ──
    st.markdown("## User Base")
    total_users = st.number_input("Total active users", min_value=10, max_value=500000, value=1000, step=100)

    # ── Tier Sizes ──
    st.markdown("## User Tiers")

    # Tier definitions shown as expander so sidebar stays clean
    with st.expander("ℹ️ What do these tiers mean?"):
        st.markdown("""
**⚡ Power users**
Actively optimise for the loyalty programme. They know the earn cap, plan activity around it, and consistently hit or approach the monthly maximum. These are your most engaged regulars who treat rewards as a meaningful incentive.
*Maps directly to your team's estimate of users who aim for the max reward — set this to 25% for "1 in 4" or 33% for "1 in 3".*

---

**◈ Mid users**
Participate when it's convenient, but don't plan around the programme. They might write a review when they genuinely want to share an opinion, or log in regularly anyway — but they're not tracking how close they are to the cap.

---

**○ Casual users**
Barely aware of the programme or simply don't care much. They may earn something incidentally (e.g. they log in anyway), but they're not changing their behaviour because of the rewards.
        """)

    pct_power = st.slider(
        "% aiming for max reward (Power users)",
        min_value=0, max_value=100, value=30, step=1,
        help="Your team estimated 1 in 3 (33%) or 1 in 4 (25%). This directly sets the Power tier size."
    )

    remaining = 100 - pct_power
    pct_mid_of_remaining = st.slider(
        "% of remaining users that are Mid (vs Casual)",
        min_value=0, max_value=100, value=60, step=1,
        help=f"Of the {remaining}% non-Power users, what share are mid-engaged vs casual? Mid users participate occasionally; casual users rarely change behaviour for rewards."
    )

    pct_mid    = round(remaining * pct_mid_of_remaining / 100)
    pct_casual = remaining - pct_mid

    # Display the resolved split
    st.markdown(f"""
    <div style="background:#13141c;border:1px solid #1f2030;border-radius:6px;padding:0.8rem 1rem;margin-top:0.3rem;font-size:0.82rem;">
        <span style="color:#c084fc">⚡ Power</span> &nbsp;{pct_power}% &nbsp;·&nbsp;
        <span style="color:#60c8f5">◈ Mid</span> &nbsp;{pct_mid}% &nbsp;·&nbsp;
        <span style="color:#7ee8a2">○ Casual</span> &nbsp;{pct_casual}%
    </div>
    """, unsafe_allow_html=True)

    # ── Participation Rates by Tier ──
    st.markdown("## Participation by Tier")
    st.caption("Of users in each tier, % who attempt each reward type")

    st.markdown('<div class="tier-header tier-power">⚡ Power</div>', unsafe_allow_html=True)
    p_review_power = st.slider("Reviews (Power)",  0, 100, 90, 1, key="rp")
    p_forum_power  = st.slider("Forum (Power)",    0, 100, 85, 1, key="fp")
    p_login_power  = st.slider("Logins (Power)",   0, 100, 95, 1, key="lp")

    st.markdown('<div class="tier-header tier-mid">◈ Mid</div>', unsafe_allow_html=True)
    p_review_mid   = st.slider("Reviews (Mid)",    0, 100, 40, 1, key="rm")
    p_forum_mid    = st.slider("Forum (Mid)",      0, 100, 30, 1, key="fm")
    p_login_mid    = st.slider("Logins (Mid)",     0, 100, 65, 1, key="lm")

    st.markdown('<div class="tier-header tier-casual">○ Casual</div>', unsafe_allow_html=True)
    p_review_casual = st.slider("Reviews (Casual)", 0, 100,  8, 1, key="rc")
    p_forum_casual  = st.slider("Forum (Casual)",   0, 100,  5, 1, key="fc")
    p_login_casual  = st.slider("Logins (Casual)",  0, 100, 40, 1, key="lc")

    # ── Intensity Multipliers ──
    st.markdown("## Intensity Multipliers")
    st.caption("Fraction of their maximum possible activity each tier actually performs")

    intensity_power  = st.slider("Power intensity",  0.0, 1.0, 0.90, 0.01,
        help="Power users chase the cap — 0.9 means they earn ~90% of the maximum possible for their activity type.")
    intensity_mid    = st.slider("Mid intensity",    0.0, 1.0, 0.50, 0.01,
        help="Mid users do roughly half of what they could. Adjust based on how engaging your rewards are.")
    intensity_casual = st.slider("Casual intensity", 0.0, 1.0, 0.15, 0.01,
        help="Casual users barely engage — mostly incidental activity like logging in anyway.")

# ── Derived budget ceilings ───────────────────────────────────────────────────
budget_reviews = monthly_earn_cap * pct_reviews / 100
budget_forum   = monthly_earn_cap * pct_forum   / 100
budget_login   = monthly_earn_cap * pct_login   / 100

# ── Tier user counts ─────────────────────────────────────────────────────────
n_power  = total_users * pct_power  / 100
n_mid    = total_users * pct_mid    / 100
n_casual = total_users * pct_casual / 100

# ── Max activity per user given budget & unit earn ───────────────────────────
# Max reviews a single user could do before hitting their personal share of budget
# (budget / earn_per_unit gives total units the pool can fund)
total_review_units_possible = budget_reviews / earn_per_review  if earn_per_review  > 0 else 0
total_forum_units_possible  = budget_forum   / earn_per_post    if earn_per_post    > 0 else 0
total_login_units_possible  = budget_login   / earn_per_login   if earn_per_login   > 0 else 0

# ── Participation counts per tier ────────────────────────────────────────────
def participants(n, pct): return n * pct / 100

rp_p = participants(n_power,  p_review_power);  rp_m = participants(n_mid, p_review_mid);  rp_c = participants(n_casual, p_review_casual)
fp_p = participants(n_power,  p_forum_power);   fp_m = participants(n_mid, p_forum_mid);   fp_c = participants(n_casual, p_forum_casual)
lp_p = participants(n_power,  p_login_power);   lp_m = participants(n_mid, p_login_mid);   lp_c = participants(n_casual, p_login_casual)

total_review_participants = rp_p + rp_m + rp_c
total_forum_participants  = fp_p + fp_m + fp_c
total_login_participants  = lp_p + lp_m + lp_c

# ── Weighted average intensity for each reward type ──────────────────────────
def weighted_intensity(p_vals, n_vals, intensities):
    total_p = sum(p * n / 100 for p, n in zip(p_vals, n_vals))
    if total_p == 0: return 0
    return sum((p * n / 100) * i for p, n, i in zip(p_vals, n_vals, intensities)) / total_p

wi_review = weighted_intensity(
    [p_review_power, p_review_mid, p_review_casual],
    [n_power, n_mid, n_casual],
    [intensity_power, intensity_mid, intensity_casual]
)
wi_forum = weighted_intensity(
    [p_forum_power, p_forum_mid, p_forum_casual],
    [n_power, n_mid, n_casual],
    [intensity_power, intensity_mid, intensity_casual]
)
wi_login = weighted_intensity(
    [p_login_power, p_login_mid, p_login_casual],
    [n_power, n_mid, n_casual],
    [intensity_power, intensity_mid, intensity_casual]
)

# ── Projected units of activity ───────────────────────────────────────────────
# Each participant earns proportionally to their intensity; total is capped by budget
projected_reviews_uncapped = total_review_participants * wi_review * (budget_reviews / max(total_review_participants, 1) / earn_per_review) if earn_per_review > 0 else 0
projected_posts_uncapped   = total_forum_participants  * wi_forum  * (budget_forum   / max(total_forum_participants,  1) / earn_per_post)   if earn_per_post   > 0 else 0
projected_logins_uncapped  = total_login_participants  * wi_login  * (budget_login   / max(total_login_participants,  1) / earn_per_login)  if earn_per_login  > 0 else 0

# Simpler direct model: avg spend per active participant × participants
avg_review_earn = (budget_reviews / max(total_review_participants, 1)) * wi_review
avg_forum_earn  = (budget_forum   / max(total_forum_participants,  1)) * wi_forum
avg_login_earn  = (budget_login   / max(total_login_participants,  1)) * wi_login

projected_review_spend = min(avg_review_earn * total_review_participants, budget_reviews)
projected_forum_spend  = min(avg_forum_earn  * total_forum_participants,  budget_forum)
projected_login_spend  = min(avg_login_earn  * total_login_participants,  budget_login)
projected_total_spend  = projected_review_spend + projected_forum_spend + projected_login_spend

projected_reviews = projected_review_spend / earn_per_review if earn_per_review > 0 else 0
projected_posts   = projected_forum_spend  / earn_per_post   if earn_per_post   > 0 else 0
projected_logins  = projected_login_spend  / earn_per_login  if earn_per_login  > 0 else 0

budget_utilisation = projected_total_spend / monthly_earn_cap * 100 if monthly_earn_cap > 0 else 0

# ── Eligible withdrawers ──────────────────────────────────────────────────────
# Users who earned >= withdrawal minimum
all_participants = set()  # conceptual: users active in at least one type
# Estimate: users in any reward = union. Since tiers are disjoint, sum uniquely
def tier_any_participant(n, pr, pf, pl):
    # P(any) ≈ 1 - P(none) = 1 - (1-pr)(1-pf)(1-pl)
    p_none = (1 - pr/100) * (1 - pf/100) * (1 - pl/100)
    return n * (1 - p_none)

any_power  = tier_any_participant(n_power,  p_review_power, p_forum_power, p_login_power)
any_mid    = tier_any_participant(n_mid,    p_review_mid,   p_forum_mid,   p_login_mid)
any_casual = tier_any_participant(n_casual, p_review_casual,p_forum_casual,p_login_casual)
total_active_participants = any_power + any_mid + any_casual

avg_earn_per_active_user = projected_total_spend / max(total_active_participants, 1)
eligible_withdrawers = total_active_participants * (avg_earn_per_active_user / max(avg_earn_per_active_user, monthly_withdraw_cap))
eligible_withdrawers = min(eligible_withdrawers, total_active_participants)
est_withdrawal_cost = eligible_withdrawers * monthly_withdraw_cap

# ── Main layout ──────────────────────────────────────────────────────────────
st.markdown("# Loyalty Engine Calculator")
st.markdown('<p style="color:#4b5563;font-size:0.88rem;margin-top:-0.5rem;">Monthly projection model · adjust parameters in the sidebar</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["  Overview  ", "  Projections  ", "  Cost Breakdown  "])

# ═══════════════════════════════════════════════════════
# TAB 1 — Overview
# ═══════════════════════════════════════════════════════
with tab1:
    # Top KPI row
    col1, col2, col3, col4 = st.columns(4)

    def kpi(col, label, value, sub=""):
        col.markdown(f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    kpi(col1, "Total Earn Pool", f"${monthly_earn_cap:,.0f}", "monthly cap")
    kpi(col2, "Projected Spend", f"${projected_total_spend:,.0f}", f"{budget_utilisation:.1f}% of pool")
    kpi(col3, "Active Participants", f"{total_active_participants:,.0f}", f"of {total_users:,} users")
    kpi(col4, "Avg Earn / User", f"${avg_earn_per_active_user:.2f}", "among active users")

    st.markdown("---")

    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.markdown('<div class="section-title">Participation breakdown by tier & reward</div>', unsafe_allow_html=True)

        tiers = ["Power", "Mid", "Casual"]
        tier_colors = ["#c084fc", "#60c8f5", "#7ee8a2"]
        n_tiers = [n_power, n_mid, n_casual]

        review_parts = [rp_p, rp_m, rp_c]
        forum_parts  = [fp_p, fp_m, fp_c]
        login_parts  = [lp_p, lp_m, lp_c]

        fig = go.Figure()
        rewards = ["Reviews", "Forum", "Logins"]
        part_data = [review_parts, forum_parts, login_parts]

        for i, (tier, color, n) in enumerate(zip(tiers, tier_colors, n_tiers)):
            vals = [part_data[r][i] for r in range(3)]
            fig.add_trace(go.Bar(
                name=tier,
                x=rewards,
                y=vals,
                marker_color=color,
                marker_line_width=0,
                opacity=0.85,
            ))

        fig.update_layout(
            barmode="stack",
            plot_bgcolor="#0e0f14",
            paper_bgcolor="#0e0f14",
            font=dict(family="DM Sans", color="#9ca3af", size=12),
            legend=dict(bgcolor="#13141c", bordercolor="#1f2030", borderwidth=1),
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            xaxis=dict(gridcolor="#1f2030", linecolor="#1f2030"),
            yaxis=dict(gridcolor="#1f2030", linecolor="#1f2030", title="# participants"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-title">Budget allocation vs. projected spend</div>', unsafe_allow_html=True)

        labels   = ["Reviews", "Forum", "Logins"]
        budgets  = [budget_reviews, budget_forum, budget_login]
        spends   = [projected_review_spend, projected_forum_spend, projected_login_spend]
        colors   = ["#c084fc", "#60c8f5", "#7ee8a2"]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Budget", x=labels, y=budgets,
                              marker_color=["#4a2d6e","#1a3d5c","#1a3d2a"],
                              marker_line_width=0))
        fig2.add_trace(go.Bar(name="Projected Spend", x=labels, y=spends,
                              marker_color=colors, marker_line_width=0, opacity=0.85))

        fig2.update_layout(
            barmode="overlay",
            plot_bgcolor="#0e0f14",
            paper_bgcolor="#0e0f14",
            font=dict(family="DM Sans", color="#9ca3af", size=12),
            legend=dict(bgcolor="#13141c", bordercolor="#1f2030", borderwidth=1),
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            xaxis=dict(gridcolor="#1f2030", linecolor="#1f2030"),
            yaxis=dict(gridcolor="#1f2030", linecolor="#1f2030", title="USD"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Budget utilisation warning
    if alloc_sum != 100:
        st.markdown(f'<div class="highlight-box">⚠️ Allocation percentages sum to <b>{alloc_sum}%</b>. Adjust to 100% for accurate projections.</div>', unsafe_allow_html=True)
    elif budget_utilisation < 50:
        st.markdown(f'<div class="highlight-box">💡 Budget utilisation is only <b>{budget_utilisation:.1f}%</b>. Consider lowering earn cap or increasing participation incentives.</div>', unsafe_allow_html=True)
    elif budget_utilisation > 95:
        st.markdown(f'<div class="highlight-box">🔥 Budget utilisation at <b>{budget_utilisation:.1f}%</b> — pool will likely be exhausted. Consider raising earn cap or tightening participation.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2 — Projections
# ═══════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">Projected activity volumes</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    kpi(col1, "Reviews / month",     f"{projected_reviews:,.0f}", f"${earn_per_review} each")
    kpi(col2, "Forum posts / month", f"{projected_posts:,.0f}",   f"${earn_per_post} each · {likes_to_qualify} likes to qualify")
    kpi(col3, "Login rewards / month", f"{projected_logins:,.0f}", f"${earn_per_login} each · {logins_per_week}×/week to qualify")

    st.markdown("---")
    st.markdown('<div class="section-title">Per-tier participation detail</div>', unsafe_allow_html=True)

    tier_data = {
        "Tier": ["⚡ Power", "◈ Mid", "○ Casual"],
        "Users": [f"{n_power:,.0f}", f"{n_mid:,.0f}", f"{n_casual:,.0f}"],
        "Review participants": [f"{rp_p:,.0f}", f"{rp_m:,.0f}", f"{rp_c:,.0f}"],
        "Forum participants": [f"{fp_p:,.0f}", f"{fp_m:,.0f}", f"{fp_c:,.0f}"],
        "Login participants": [f"{lp_p:,.0f}", f"{lp_m:,.0f}", f"{lp_c:,.0f}"],
        "Intensity": [f"{intensity_power*100:.0f}%", f"{intensity_mid*100:.0f}%", f"{intensity_casual*100:.0f}%"],
    }
    df_tiers = pd.DataFrame(tier_data)
    st.dataframe(df_tiers, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Sensitivity: projected spend vs. total users</div>', unsafe_allow_html=True)

    user_range = np.linspace(max(10, total_users * 0.1), total_users * 3, 60)
    scale = user_range / total_users

    spend_r = np.minimum(projected_review_spend * scale, budget_reviews)
    spend_f = np.minimum(projected_forum_spend  * scale, budget_forum)
    spend_l = np.minimum(projected_login_spend  * scale, budget_login)
    spend_t = spend_r + spend_f + spend_l

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=user_range, y=spend_r, name="Reviews",  line=dict(color="#c084fc", width=2)))
    fig3.add_trace(go.Scatter(x=user_range, y=spend_f, name="Forum",    line=dict(color="#60c8f5", width=2)))
    fig3.add_trace(go.Scatter(x=user_range, y=spend_l, name="Logins",   line=dict(color="#7ee8a2", width=2)))
    fig3.add_trace(go.Scatter(x=user_range, y=spend_t, name="Total",    line=dict(color="#f59e0b", width=2.5, dash="dot")))
    fig3.add_vline(x=total_users, line_dash="dash", line_color="#4b5563",
                   annotation_text="Current", annotation_font_color="#6b7280")
    fig3.add_hline(y=monthly_earn_cap, line_dash="dash", line_color="#ef4444",
                   annotation_text="Earn Cap", annotation_font_color="#ef4444")

    fig3.update_layout(
        plot_bgcolor="#0e0f14", paper_bgcolor="#0e0f14",
        font=dict(family="DM Sans", color="#9ca3af", size=12),
        legend=dict(bgcolor="#13141c", bordercolor="#1f2030", borderwidth=1),
        margin=dict(l=0, r=0, t=20, b=0), height=320,
        xaxis=dict(gridcolor="#1f2030", linecolor="#1f2030", title="Total active users"),
        yaxis=dict(gridcolor="#1f2030", linecolor="#1f2030", title="Projected spend (USD)"),
    )
    st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 3 — Cost Breakdown
# ═══════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Monthly cost summary</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    kpi(col1, "Review spend",    f"${projected_review_spend:,.2f}", f"{projected_review_spend/monthly_earn_cap*100:.1f}% of pool")
    kpi(col2, "Forum spend",     f"${projected_forum_spend:,.2f}",  f"{projected_forum_spend/monthly_earn_cap*100:.1f}% of pool")
    kpi(col3, "Login spend",     f"${projected_login_spend:,.2f}",  f"{projected_login_spend/monthly_earn_cap*100:.1f}% of pool")
    kpi(col4, "Total projected", f"${projected_total_spend:,.2f}",  f"of ${monthly_earn_cap:,} cap")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Spend distribution (donut)</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Pie(
            labels=["Reviews", "Forum", "Logins", "Unused"],
            values=[
                projected_review_spend,
                projected_forum_spend,
                projected_login_spend,
                max(monthly_earn_cap - projected_total_spend, 0)
            ],
            hole=0.6,
            marker=dict(colors=["#c084fc", "#60c8f5", "#7ee8a2", "#1f2030"]),
            textinfo="label+percent",
            textfont=dict(family="Space Mono", size=11),
        ))
        fig4.update_layout(
            plot_bgcolor="#0e0f14", paper_bgcolor="#0e0f14",
            font=dict(family="DM Sans", color="#9ca3af"),
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0), height=280,
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Withdrawal estimate</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:0.8rem">
            <div class="label">Active participants (any reward)</div>
            <div class="value">{total_active_participants:,.0f}</div>
            <div class="sub">of {total_users:,} total users</div>
        </div>
        <div class="metric-card" style="margin-bottom:0.8rem">
            <div class="label">Avg earn per active user</div>
            <div class="value">${avg_earn_per_active_user:.2f}</div>
            <div class="sub">Min withdrawal: ${monthly_withdraw_cap}</div>
        </div>
        <div class="metric-card">
            <div class="label">Est. withdrawal-eligible users</div>
            <div class="value">{eligible_withdrawers:,.0f}</div>
            <div class="sub">Est. withdrawal cost: ${est_withdrawal_cost:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">Full cost table</div>', unsafe_allow_html=True)

    cost_df = pd.DataFrame({
        "Reward Type": ["Reviews", "Forum Posts", "Login Streaks", "Total"],
        "Budget ($)": [f"${budget_reviews:,.2f}", f"${budget_forum:,.2f}", f"${budget_login:,.2f}", f"${monthly_earn_cap:,.2f}"],
        "Projected Spend ($)": [f"${projected_review_spend:,.2f}", f"${projected_forum_spend:,.2f}", f"${projected_login_spend:,.2f}", f"${projected_total_spend:,.2f}"],
        "Utilisation": [f"{projected_review_spend/budget_reviews*100:.1f}%" if budget_reviews>0 else "—",
                        f"{projected_forum_spend/budget_forum*100:.1f}%"   if budget_forum>0   else "—",
                        f"{projected_login_spend/budget_login*100:.1f}%"   if budget_login>0   else "—",
                        f"{budget_utilisation:.1f}%"],
        "Participants": [f"{total_review_participants:,.0f}", f"{total_forum_participants:,.0f}", f"{total_login_participants:,.0f}", f"{total_active_participants:,.0f}"],
        "Units rewarded": [f"{projected_reviews:,.0f}", f"{projected_posts:,.0f}", f"{projected_logins:,.0f}", "—"],
    })
    st.dataframe(cost_df, use_container_width=True, hide_index=True)