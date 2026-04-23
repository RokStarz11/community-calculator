import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
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

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Space Mono', monospace !important; }

.stApp { background-color: #0e0f14; color: #e8e9f0; }

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
.metric-card .sub { font-size: 0.78rem; color: #4b5563; margin-top: 0.3rem; }

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

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# ⚙️ Loyalty Engine")
    st.markdown("---")

    st.markdown("## Reward Caps")
    monthly_earn_cap     = st.number_input("Max a user can earn per month (USD)", min_value=10, max_value=500, value=100, step=10,
        help="The ceiling on how much loyalty rewards a single user can accumulate in one calendar month.")
    monthly_withdraw_cap = st.number_input("Min balance to request a payout (USD)", min_value=1, max_value=500, value=20, step=5,
        help="A user can only withdraw once their accumulated balance reaches this threshold.")

    st.markdown("## Reward Structure")
    pct_reviews = st.slider("% of earn cap → Reviews", 0, 100, 80, 1)
    pct_forum   = st.slider("% of earn cap → Forum",   0, 100, 15, 1)
    pct_login   = st.slider("% of earn cap → Logins",  0, 100,  5, 1)

    alloc_sum = pct_reviews + pct_forum + pct_login
    if alloc_sum != 100:
        st.warning(f"Reward structure sums to {alloc_sum}% (should be 100%)")

    st.markdown("## Rewards")
    earn_per_review = st.number_input("Earn per confirmed review (USD)",      min_value=1,   max_value=50,   value=8,   step=1)
    earn_per_post   = st.number_input("Earn per qualifying forum post (USD)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
    earn_per_login  = st.number_input("Earn per weekly login reward (USD)",   min_value=0.1, max_value=20.0, value=1.0, step=0.1)

    st.markdown("## Qualification Rules")
    likes_to_qualify = st.number_input("Likes needed per forum post to qualify", min_value=0, max_value=50, value=5, step=1)
    logins_per_week  = st.number_input("Logins/week to qualify for login reward", min_value=1, max_value=7, value=3, step=1)

    st.markdown("## User Base")
    total_users_m1 = st.number_input("Total active users on month 1", min_value=10, max_value=500000, value=1000, step=100,
        help="All users counted here are considered active — they participate in at least some loyalty activity.")

    st.markdown("## User Tiers")
    with st.expander("ℹ️ What do these tiers mean?"):
        st.markdown("""
**⚡ Power users**
Actively optimise for the loyalty programme. They know the earn cap, plan activity around it, and consistently hit or approach the monthly maximum.
*Set to 25% for "1 in 4" or 33% for "1 in 3" — matches your team's estimate directly.*

---
**◈ Mid users**
Participate when convenient but don't plan around the programme. They write reviews when they genuinely want to, log in regularly anyway — but aren't tracking their cap.

---
**○ Casual users**
Barely aware of the programme or don't care much. They may earn something incidentally but aren't changing their behaviour because of rewards.
        """)

    pct_power = st.slider(
        "% aiming for max reward (Power users)", 0, 100, 30, 1,
        help="Your team estimated 1 in 3 (33%) or 1 in 4 (25%). This sets the Power tier directly."
    )
    remaining = 100 - pct_power
    pct_mid_of_remaining = st.slider(
        "% of remaining users that are Mid (vs Casual)", 0, 100, 60, 1,
        help=f"Of the {remaining}% non-Power users, what share are mid-engaged vs casual?"
    )
    pct_mid    = round(remaining * pct_mid_of_remaining / 100)
    pct_casual = remaining - pct_mid

    st.markdown(f"""
    <div style="background:#13141c;border:1px solid #1f2030;border-radius:6px;
                padding:0.8rem 1rem;margin-top:0.3rem;font-size:0.82rem;">
        <span style="color:#c084fc">⚡ Power</span> &nbsp;{pct_power}% &nbsp;·&nbsp;
        <span style="color:#60c8f5">◈ Mid</span> &nbsp;{pct_mid}% &nbsp;·&nbsp;
        <span style="color:#7ee8a2">○ Casual</span> &nbsp;{pct_casual}%
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Participation by Tier")
    st.caption("Of users in each tier, % who attempt each reward type")

    st.markdown('<div class="tier-header tier-power">⚡ Power</div>', unsafe_allow_html=True)
    p_review_power = st.slider("Reviews (Power)", 0, 100, 90, 1, key="rp")
    p_forum_power  = st.slider("Forum (Power)",   0, 100, 85, 1, key="fp")
    p_login_power  = st.slider("Logins (Power)",  0, 100, 95, 1, key="lp")

    st.markdown('<div class="tier-header tier-mid">◈ Mid</div>', unsafe_allow_html=True)
    p_review_mid   = st.slider("Reviews (Mid)",   0, 100, 40, 1, key="rm")
    p_forum_mid    = st.slider("Forum (Mid)",     0, 100, 30, 1, key="fm")
    p_login_mid    = st.slider("Logins (Mid)",    0, 100, 65, 1, key="lm")

    st.markdown('<div class="tier-header tier-casual">○ Casual</div>', unsafe_allow_html=True)
    p_review_casual = st.slider("Reviews (Casual)", 0, 100,  8, 1, key="rc")
    p_forum_casual  = st.slider("Forum (Casual)",   0, 100,  5, 1, key="fc")
    p_login_casual  = st.slider("Logins (Casual)",  0, 100, 40, 1, key="lc")

    st.markdown("## Intensity Multipliers")
    st.caption("Fraction of the monthly earn cap each tier actually reaches")
    intensity_power  = st.slider("Power intensity",  0.0, 1.0, 0.90, 0.01,
        help="Power users chase the cap — 0.9 means they earn ~90% of monthly_earn_cap.")
    intensity_mid    = st.slider("Mid intensity",    0.0, 1.0, 0.50, 0.01,
        help="Mid users do roughly half of what they could.")
    intensity_casual = st.slider("Casual intensity", 0.0, 1.0, 0.15, 0.01,
        help="Casual users barely engage — mostly incidental activity.")

    st.markdown("## Simulation")
    sim_months      = st.slider("Months to simulate", 2, 24, 12, 1)
    user_growth_pct = st.slider("Monthly user growth (%)", 0.0, 30.0, 5.0, 0.5,
        help="% of new active users added each month. New users always start with a zero balance.")


# ── Per-user earn amounts ─────────────────────────────────────────────────────
# Each user earns up to monthly_earn_cap. Their actual earn = intensity × cap.
earn_power  = monthly_earn_cap * intensity_power
earn_mid    = monthly_earn_cap * intensity_mid
earn_casual = monthly_earn_cap * intensity_casual

avg_earn_per_user = (
    earn_power  * pct_power  / 100 +
    earn_mid    * pct_mid    / 100 +
    earn_casual * pct_casual / 100
)

# Tier user counts (month 1)
n_power_m1  = total_users_m1 * pct_power  / 100
n_mid_m1    = total_users_m1 * pct_mid    / 100
n_casual_m1 = total_users_m1 * pct_casual / 100

# Participation counts (month 1, for display)
def part(n, pct): return n * pct / 100
rp_p = part(n_power_m1, p_review_power); rp_m = part(n_mid_m1, p_review_mid); rp_c = part(n_casual_m1, p_review_casual)
fp_p = part(n_power_m1, p_forum_power);  fp_m = part(n_mid_m1, p_forum_mid);  fp_c = part(n_casual_m1, p_forum_casual)
lp_p = part(n_power_m1, p_login_power);  lp_m = part(n_mid_m1, p_login_mid);  lp_c = part(n_casual_m1, p_login_casual)

total_review_part_m1 = rp_p + rp_m + rp_c
total_forum_part_m1  = fp_p + fp_m + fp_c
total_login_part_m1  = lp_p + lp_m + lp_c

# Month 1 totals
total_earn_pool_m1    = monthly_earn_cap * total_users_m1
projected_spend_m1    = avg_earn_per_user * total_users_m1
budget_util_m1        = projected_spend_m1 / total_earn_pool_m1 * 100 if total_earn_pool_m1 > 0 else 0

projected_review_spend_m1 = projected_spend_m1 * pct_reviews / 100
projected_forum_spend_m1  = projected_spend_m1 * pct_forum   / 100
projected_login_spend_m1  = projected_spend_m1 * pct_login   / 100

projected_reviews_m1 = projected_review_spend_m1 / earn_per_review if earn_per_review > 0 else 0
projected_posts_m1   = projected_forum_spend_m1  / earn_per_post   if earn_per_post   > 0 else 0
projected_logins_m1  = projected_login_spend_m1  / earn_per_login  if earn_per_login  > 0 else 0


# ── Multi-month simulation ────────────────────────────────────────────────────
# Users accumulate a balance each month equal to their tier's earn amount.
# When balance >= monthly_withdraw_cap they cash out (balance resets to 0).
# New users join each month with balance = 0.
# Cohorts: all users who joined in the same month and share the same tier
# have identical earn rates, so we track (count, balance) per cohort.

def run_simulation(months, total_m1, growth_pct, ep, em, ec, pp, pm, pc, withdraw_min):
    cohorts = {"power": [], "mid": [], "casual": []}  # each entry: [n_users, balance]
    earn    = {"power": ep, "mid": em, "casual": ec}
    tier_pct = {"power": pp/100, "mid": pm/100, "casual": pc/100}

    rows = []
    prev_total = 0

    for month in range(1, months + 1):
        new_users = total_m1 if month == 1 else round(prev_total * growth_pct / 100)

        # Add new cohort
        for tier in cohorts:
            n = new_users * tier_pct[tier]
            if n > 0:
                cohorts[tier].append([n, 0.0])

        # Earn this month
        for tier, cohort_list in cohorts.items():
            for cohort in cohort_list:
                cohort[1] = min(cohort[1] + earn[tier], monthly_earn_cap * 12)

        # Process payouts
        total_payout      = 0.0
        total_payout_users = 0
        for cohort_list in cohorts.values():
            for cohort in cohort_list:
                if cohort[1] >= withdraw_min:
                    total_payout       += cohort[0] * cohort[1]
                    total_payout_users += cohort[0]
                    cohort[1]           = 0.0

        # Totals this month
        total_users_now = sum(c[0] for cl in cohorts.values() for c in cl)
        earned_now      = sum(c[0] * earn[tier] for tier, cl in cohorts.items() for c in cl)
        pool_now        = monthly_earn_cap * total_users_now
        avg_payout      = total_payout / total_payout_users if total_payout_users > 0 else 0.0

        rows.append({
            "Month":           month,
            "Total users":     round(total_users_now),
            "New users":       round(new_users),
            "Earn pool":       round(pool_now, 2),
            "Projected spend": round(earned_now, 2),
            "Payout users":    round(total_payout_users),
            "Total payout":    round(total_payout, 2),
            "Avg payout/user": round(avg_payout, 2),
        })
        prev_total = total_users_now

    return pd.DataFrame(rows)


sim_df = run_simulation(
    sim_months, total_users_m1, user_growth_pct,
    earn_power, earn_mid, earn_casual,
    pct_power, pct_mid, pct_casual,
    monthly_withdraw_cap
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def kpi(col, label, value, sub=""):
    col.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

BASE_LAYOUT = dict(
    plot_bgcolor="#0e0f14", paper_bgcolor="#0e0f14",
    font=dict(family="DM Sans", color="#9ca3af", size=12),
    legend=dict(bgcolor="#13141c", bordercolor="#1f2030", borderwidth=1),
    margin=dict(l=0, r=0, t=20, b=0),
)
AXIS = dict(gridcolor="#1f2030", linecolor="#1f2030")


# ── Tabs ──────────────────────────────────────────────────────────────────────
st.markdown("# Loyalty Engine Calculator")
st.markdown('<p style="color:#4b5563;font-size:0.88rem;margin-top:-0.5rem;">Monthly projection model · adjust parameters in the sidebar</p>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["  Overview  ", "  Projections  ", "  Cost Breakdown  ", "  Simulation  ", "  Scenarios  "])


# ═══════════════════════════════════════════════════════
# TAB 1 — Overview
# ═══════════════════════════════════════════════════════
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    kpi(col1, "Total Earn Pool (mo. 1)", f"${total_earn_pool_m1:,.0f}",  f"{total_users_m1:,} users × ${monthly_earn_cap} cap")
    kpi(col2, "Projected Spend (mo. 1)", f"${projected_spend_m1:,.0f}",  f"{budget_util_m1:.1f}% of pool")
    kpi(col3, "Active Users (mo. 1)",    f"{total_users_m1:,}",          "all counted as active")
    kpi(col4, "Avg Earn / User (mo. 1)", f"${avg_earn_per_user:.2f}",    f"vs ${monthly_earn_cap} cap · min payout ${monthly_withdraw_cap}")

    st.markdown("---")
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.markdown('<div class="section-title">Participation breakdown by tier & reward (month 1)</div>', unsafe_allow_html=True)
        fig = go.Figure()
        for tier, color, vals in [
            ("Power",  "#c084fc", [rp_p, fp_p, lp_p]),
            ("Mid",    "#60c8f5", [rp_m, fp_m, lp_m]),
            ("Casual", "#7ee8a2", [rp_c, fp_c, lp_c]),
        ]:
            fig.add_trace(go.Bar(name=tier, x=["Reviews", "Forum", "Logins"], y=vals,
                                 marker_color=color, marker_line_width=0, opacity=0.85))
        fig.update_layout(**BASE_LAYOUT, barmode="stack", height=300,
                          xaxis=AXIS, yaxis=dict(**AXIS, title="# users"))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-title">Earn cap vs. projected earn / user</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="Earn cap",
            x=["Power", "Mid", "Casual"],
            y=[monthly_earn_cap] * 3,
            marker_color=["#4a2d6e", "#1a3d5c", "#1a3d2a"], marker_line_width=0
        ))
        fig2.add_trace(go.Bar(
            name="Projected earn",
            x=["Power", "Mid", "Casual"],
            y=[earn_power, earn_mid, earn_casual],
            marker_color=["#c084fc", "#60c8f5", "#7ee8a2"], marker_line_width=0, opacity=0.85
        ))
        fig2.update_layout(**BASE_LAYOUT, barmode="overlay", height=300,
                           xaxis=AXIS, yaxis=dict(**AXIS, title="USD / user / month"))
        st.plotly_chart(fig2, use_container_width=True)

    if alloc_sum != 100:
        st.markdown(f'<div class="highlight-box">⚠️ Reward structure sums to <b>{alloc_sum}%</b>. Adjust to 100% for accurate projections.</div>', unsafe_allow_html=True)
    elif budget_util_m1 < 50:
        st.markdown(f'<div class="highlight-box">💡 Only <b>{budget_util_m1:.1f}%</b> of the earn pool is projected to be used. Consider raising reward amounts or intensity.</div>', unsafe_allow_html=True)
    elif budget_util_m1 > 95:
        st.markdown(f'<div class="highlight-box">🔥 Projected spend is <b>{budget_util_m1:.1f}%</b> of pool — close to the ceiling. Monitor closely as user base grows.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2 — Projections
# ═══════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">Rewarded activity volumes (month 1)</div>', unsafe_allow_html=True)
    st.markdown('<div class="highlight-box">These figures count activity that falls within reward limits and gets paid out — not total activity submitted. Any reviews, posts, or logins beyond a user\'s earn cap are not counted here, as the current model assumes activity stays within those limits.</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    kpi(col1, "Reviews rewarded",       f"{projected_reviews_m1:,.0f}", f"${earn_per_review} each · within earn cap")
    kpi(col2, "Forum posts rewarded",   f"{projected_posts_m1:,.0f}",   f"${earn_per_post} each · {likes_to_qualify} likes to qualify")
    kpi(col3, "Login rewards paid out", f"{projected_logins_m1:,.0f}",  f"${earn_per_login} each · {logins_per_week}×/week to qualify")

    st.markdown("---")
    st.markdown('<div class="section-title">Per-tier detail (month 1)</div>', unsafe_allow_html=True)
    tier_df = pd.DataFrame({
        "Tier":                ["⚡ Power", "◈ Mid", "○ Casual"],
        "Users":               [f"{n_power_m1:,.0f}", f"{n_mid_m1:,.0f}", f"{n_casual_m1:,.0f}"],
        "Earn / user / mo":    [f"${earn_power:.2f}", f"${earn_mid:.2f}", f"${earn_casual:.2f}"],
        "Review participants": [f"{rp_p:,.0f}", f"{rp_m:,.0f}", f"{rp_c:,.0f}"],
        "Forum participants":  [f"{fp_p:,.0f}", f"{fp_m:,.0f}", f"{fp_c:,.0f}"],
        "Login participants":  [f"{lp_p:,.0f}", f"{lp_m:,.0f}", f"{lp_c:,.0f}"],
        "Intensity":           [f"{intensity_power*100:.0f}%", f"{intensity_mid*100:.0f}%", f"{intensity_casual*100:.0f}%"],
    })
    st.dataframe(tier_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Sensitivity: projected spend vs. user base size</div>', unsafe_allow_html=True)
    user_range = np.linspace(max(10, total_users_m1 * 0.1), total_users_m1 * 3, 60)
    scale      = user_range / total_users_m1

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=user_range, y=projected_review_spend_m1 * scale, name="Reviews", line=dict(color="#c084fc", width=2)))
    fig3.add_trace(go.Scatter(x=user_range, y=projected_forum_spend_m1  * scale, name="Forum",   line=dict(color="#60c8f5", width=2)))
    fig3.add_trace(go.Scatter(x=user_range, y=projected_login_spend_m1  * scale, name="Logins",  line=dict(color="#7ee8a2", width=2)))
    fig3.add_trace(go.Scatter(x=user_range, y=projected_spend_m1        * scale, name="Total",   line=dict(color="#f59e0b", width=2.5, dash="dot")))
    fig3.add_vline(x=total_users_m1, line_dash="dash", line_color="#4b5563",
                   annotation_text="Month 1", annotation_font_color="#6b7280")
    fig3.add_hline(y=total_earn_pool_m1, line_dash="dash", line_color="#ef4444",
                   annotation_text="Earn pool ceiling (mo.1)", annotation_font_color="#ef4444")
    fig3.update_layout(**BASE_LAYOUT, height=320,
                       xaxis=dict(**AXIS, title="Total active users"),
                       yaxis=dict(**AXIS, title="Projected spend (USD)"))
    st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 3 — Cost Breakdown
# ═══════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Month 1 cost summary</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    kpi(col1, "Review spend",    f"${projected_review_spend_m1:,.2f}", f"{pct_reviews}% of spend")
    kpi(col2, "Forum spend",     f"${projected_forum_spend_m1:,.2f}",  f"{pct_forum}% of spend")
    kpi(col3, "Login spend",     f"${projected_login_spend_m1:,.2f}",  f"{pct_login}% of spend")
    kpi(col4, "Total projected", f"${projected_spend_m1:,.2f}",        f"of ${total_earn_pool_m1:,.0f} pool")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Spend distribution (month 1)</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Pie(
            labels=["Reviews", "Forum", "Logins", "Unused"],
            values=[
                projected_review_spend_m1,
                projected_forum_spend_m1,
                projected_login_spend_m1,
                max(total_earn_pool_m1 - projected_spend_m1, 0),
            ],
            hole=0.6,
            marker=dict(colors=["#c084fc", "#60c8f5", "#7ee8a2", "#1f2030"]),
            textinfo="label+percent",
            textfont=dict(family="Space Mono", size=11),
        ))
        fig4.update_layout(plot_bgcolor="#0e0f14", paper_bgcolor="#0e0f14",
                           font=dict(family="DM Sans", color="#9ca3af"),
                           showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=280)
        st.plotly_chart(fig4, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Full cost table (month 1)</div>', unsafe_allow_html=True)
        pool_r = total_earn_pool_m1 * pct_reviews / 100
        pool_f = total_earn_pool_m1 * pct_forum   / 100
        pool_l = total_earn_pool_m1 * pct_login   / 100
        cost_df = pd.DataFrame({
            "Reward Type":       ["Reviews", "Forum Posts", "Login Streaks", "Total"],
            "Earn pool (USD)":   [f"${pool_r:,.2f}", f"${pool_f:,.2f}", f"${pool_l:,.2f}", f"${total_earn_pool_m1:,.2f}"],
            "Proj. spend (USD)": [f"${projected_review_spend_m1:,.2f}", f"${projected_forum_spend_m1:,.2f}",
                                  f"${projected_login_spend_m1:,.2f}", f"${projected_spend_m1:,.2f}"],
            "Utilisation":       [f"{projected_review_spend_m1/pool_r*100:.1f}%" if pool_r > 0 else "—",
                                  f"{projected_forum_spend_m1/pool_f*100:.1f}%"  if pool_f > 0 else "—",
                                  f"{projected_login_spend_m1/pool_l*100:.1f}%"  if pool_l > 0 else "—",
                                  f"{budget_util_m1:.1f}%"],
            "Participants":      [f"{total_review_part_m1:,.0f}", f"{total_forum_part_m1:,.0f}",
                                  f"{total_login_part_m1:,.0f}", f"{total_users_m1:,}"],
            "Units rewarded":    [f"{projected_reviews_m1:,.0f}", f"{projected_posts_m1:,.0f}",
                                  f"{projected_logins_m1:,.0f}", "—"],
        })
        st.dataframe(cost_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════
# TAB 4 — Simulation
# ═══════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-title">Monthly simulation overview</div>', unsafe_allow_html=True)

    last = sim_df.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    kpi(col1, f"Total users (mo. {sim_months})",   f"{last['Total users']:,}",
        f"+{user_growth_pct}%/mo from {total_users_m1:,}")
    kpi(col2, f"Earn pool (mo. {sim_months})",      f"${last['Earn pool']:,.0f}",
        f"${monthly_earn_cap} cap × {last['Total users']:,} users")
    kpi(col3, f"Proj. spend (mo. {sim_months})",    f"${last['Projected spend']:,.0f}",
        f"{last['Projected spend']/last['Earn pool']*100:.1f}% of pool")
    kpi(col4, f"Payout users (mo. {sim_months})",   f"{last['Payout users']:,}",
        f"avg ${last['Avg payout/user']:.2f} each · min ${monthly_withdraw_cap}")

    st.markdown("---")

    # Chart 1 — Earn pool vs projected spend
    st.markdown('<div class="section-title">Earn pool vs. projected spend over time</div>', unsafe_allow_html=True)
    fig_s1 = go.Figure()
    fig_s1.add_trace(go.Scatter(
        x=sim_df["Month"], y=sim_df["Earn pool"],
        name="Earn pool", line=dict(color="#374151", width=2),
        fill="tozeroy", fillcolor="rgba(55,65,81,0.2)"
    ))
    fig_s1.add_trace(go.Scatter(
        x=sim_df["Month"], y=sim_df["Projected spend"],
        name="Projected spend", line=dict(color="#7ee8a2", width=2.5)
    ))
    fig_s1.update_layout(**BASE_LAYOUT, height=280,
                         xaxis=dict(**AXIS, title="Month", dtick=1),
                         yaxis=dict(**AXIS, title="USD"))
    st.plotly_chart(fig_s1, use_container_width=True)

    col_l, col_r = st.columns(2)

    with col_l:
        # Chart 2 — Payout users vs total users
        st.markdown('<div class="section-title">Payout-eligible users vs. total users</div>', unsafe_allow_html=True)
        fig_s2 = go.Figure()
        fig_s2.add_trace(go.Bar(x=sim_df["Month"], y=sim_df["Total users"],
                                name="Total users", marker_color="#1f2030", marker_line_width=0))
        fig_s2.add_trace(go.Bar(x=sim_df["Month"], y=sim_df["Payout users"],
                                name=f"Above ${monthly_withdraw_cap} threshold",
                                marker_color="#60c8f5", marker_line_width=0, opacity=0.85))
        fig_s2.update_layout(**BASE_LAYOUT, barmode="overlay", height=280,
                             xaxis=dict(**AXIS, title="Month", dtick=1),
                             yaxis=dict(**AXIS, title="# users"))
        st.plotly_chart(fig_s2, use_container_width=True)

    with col_r:
        # Chart 3 — Total payout & avg payout/user
        st.markdown('<div class="section-title">Total payout & avg payout / eligible user</div>', unsafe_allow_html=True)
        fig_s3 = go.Figure()
        fig_s3.add_trace(go.Bar(x=sim_df["Month"], y=sim_df["Total payout"],
                                name="Total payout (USD)", marker_color="#c084fc",
                                marker_line_width=0, opacity=0.85))
        fig_s3.add_trace(go.Scatter(x=sim_df["Month"], y=sim_df["Avg payout/user"],
                                    name="Avg payout / user (USD)",
                                    line=dict(color="#f59e0b", width=2), yaxis="y2"))
        fig_s3.update_layout(
            **BASE_LAYOUT, height=280,
            xaxis=dict(**AXIS, title="Month", dtick=1),
            yaxis=dict(**AXIS, title="Total payout (USD)"),
            yaxis2=dict(overlaying="y", side="right", title="Avg / user (USD)",
                        gridcolor="#1f2030", linecolor="#1f2030", showgrid=False),
        )
        st.plotly_chart(fig_s3, use_container_width=True)

    # Chart 4 — User growth
    st.markdown('<div class="section-title">User base growth</div>', unsafe_allow_html=True)
    fig_s4 = go.Figure()
    fig_s4.add_trace(go.Scatter(
        x=sim_df["Month"], y=sim_df["Total users"],
        name="Total users", line=dict(color="#7ee8a2", width=2.5),
        fill="tozeroy", fillcolor="rgba(126,232,162,0.07)"
    ))
    fig_s4.add_trace(go.Bar(
        x=sim_df["Month"], y=sim_df["New users"],
        name="New users this month", marker_color="#60c8f5",
        marker_line_width=0, opacity=0.6
    ))
    fig_s4.update_layout(**BASE_LAYOUT, barmode="overlay", height=260,
                         xaxis=dict(**AXIS, title="Month", dtick=1),
                         yaxis=dict(**AXIS, title="# users"))
    st.plotly_chart(fig_s4, use_container_width=True)

    # Full table
    st.markdown('<div class="section-title">Full simulation table</div>', unsafe_allow_html=True)
    display_df = sim_df.copy()
    for col in ["Earn pool", "Projected spend", "Total payout", "Avg payout/user"]:
        display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
    for col in ["Total users", "New users", "Payout users"]:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════
# TAB 5 — Scenarios
# ═══════════════════════════════════════════════════════

# ── Scenario parameters (hardcoded from our conversation) ────────────────────
#
# ACQUISITION FUNNEL (monthly new community subscribers)
#   Main site:        10,000 visitors × 80% exposure × 10% click × 20% subscribe = 160
#   Affiliate sites:  10,400 visitors × 80% exposure × 10% click × 15% subscribe = 125
#   Base total:       ~285/month
#   Optimistic boost: 2.5× from month 3 (forum/partner/word-of-mouth effect)
#
# ACTIVE MEMBER RETENTION: 10% of all subscribers remain active long-term
#
# CONVERSION TO DEPOSITOR (of active members):
#   Pessimistic: 30% by month 6,  50% by month 12  → ~4.2%/month ramp
#   Optimistic:  50% by month 6,  75% by month 12  → ~7.1%/month ramp
#
# DEPOSITOR LTV: $375 accruing over 6 months = $62.50/month per converted depositor
#
# SEO BASELINE REVENUE: $100,000/month (unaffected by community)
#
# LOYALTY COSTS: derived from simulation — avg earn per active user × active users
#   Earn cap: $100/user/month, withdrawal min: $100
#   Power (10%): intensity 1.0 → $100/mo
#   Mid   (54%): intensity 0.5 → $50/mo   [60% of remaining 90%]
#   Casual(36%): intensity 0.15→ $15/mo   [40% of remaining 90%]
#   Weighted avg earn/active user = 0.10×100 + 0.54×50 + 0.36×15 = $42.40
#
# WITHDRAWAL MINIMUM NOTE:
#   Power users ($100/mo earn) hit withdrawal threshold every month ✓
#   Mid users   ($50/mo earn)  hit threshold every 2 months ✓
#   Casual users($15/mo earn)  hit threshold after ~7 months — risk of disengagement

SEO_REVENUE        = 100_000   # per month, constant
LTV_PER_DEPOSITOR  = 375       # lifetime value
LTV_MONTHS         = 6         # accrual period
LTV_PER_MONTH      = LTV_PER_DEPOSITOR / LTV_MONTHS   # $62.50/month per depositor

BASE_SUBS_PER_MONTH = 285      # base new subscribers/month
ACTIVE_RETENTION    = 0.10     # 10% of all-time subscribers become/stay active

# Weighted avg loyalty cost per active user per month
EARN_POWER   = 100.0
EARN_MID     = 50.0
EARN_CASUAL  = 15.0
PCT_POWER_SC = 0.10
PCT_MID_SC   = 0.54
PCT_CASUAL_SC= 0.36
AVG_EARN_ACTIVE = PCT_POWER_SC * EARN_POWER + PCT_MID_SC * EARN_MID + PCT_CASUAL_SC * EARN_CASUAL

# Withdrawal: power cash out monthly, mid every 2 months, casual ~month 7+
# We model actual monthly payout = fraction of earned that becomes payable
# Power: 100% pays out monthly; Mid: 50% pays out monthly (avg); Casual: ~14% (1/7)
PAYOUT_RATE_POWER   = 1.00
PAYOUT_RATE_MID     = 0.50
PAYOUT_RATE_CASUAL  = 0.14

AVG_PAYOUT_ACTIVE = (
    PCT_POWER_SC  * EARN_POWER  * PAYOUT_RATE_POWER  +
    PCT_MID_SC    * EARN_MID    * PAYOUT_RATE_MID    +
    PCT_CASUAL_SC * EARN_CASUAL * PAYOUT_RATE_CASUAL
)


def build_scenario(label, sub_multiplier_from_m3, conv_rate_m6, conv_rate_m12):
    """
    Build a 12-month P&L for one scenario.
    sub_multiplier_from_m3: multiplier on base subs from month 3 onward
    conv_rate_m6:  cumulative % of active members converted by month 6
    conv_rate_m12: cumulative % of active members converted by month 12
    """
    rows = []
    cumulative_subs   = 0
    active_members    = 0
    # Track depositors that are still within their 6-month LTV accrual window
    # depositor_cohorts: list of (month_converted, count) — we pay LTV/6 per month for 6mo
    depositor_cohorts = []

    # Monthly conversion rate: interpolate linearly between 0 → m6 rate → m12 rate
    def monthly_conv_rate(month):
        if month <= 6:
            # ramp from 0 to conv_rate_m6 over 6 months
            return (conv_rate_m6 / 6)
        else:
            # ramp from conv_rate_m6 to conv_rate_m12 over next 6 months
            extra = (conv_rate_m12 - conv_rate_m6) / 6
            return extra

    for m in range(1, 13):
        # New subscribers this month
        if m < 3:
            new_subs = BASE_SUBS_PER_MONTH
        else:
            new_subs = round(BASE_SUBS_PER_MONTH * sub_multiplier_from_m3)

        cumulative_subs += new_subs
        active_members   = round(cumulative_subs * ACTIVE_RETENTION)

        # New depositors this month = active members × monthly conversion rate
        # (only unconverted active members convert — approximation: assume pool stays large)
        new_depositors = active_members * monthly_conv_rate(m)
        depositor_cohorts.append(new_depositors)

        # Community revenue: sum LTV/6 for each cohort still within accrual window
        community_rev = 0.0
        for age, cohort_size in enumerate(reversed(depositor_cohorts)):
            if age < LTV_MONTHS:
                community_rev += cohort_size * LTV_PER_MONTH

        # Loyalty costs (actual payouts this month)
        loyalty_cost = active_members * AVG_PAYOUT_ACTIVE

        # Total revenue and net
        total_rev     = SEO_REVENUE + community_rev
        net_community = community_rev - loyalty_cost

        rows.append({
            "Month":             m,
            "New subscribers":   round(new_subs),
            "Total subscribers": round(cumulative_subs),
            "Active members":    active_members,
            "New depositors":    round(new_depositors),
            "Community revenue": round(community_rev, 2),
            "Loyalty cost":      round(loyalty_cost, 2),
            "Net community":     round(net_community, 2),
            "SEO revenue":       SEO_REVENUE,
            "Total revenue":     round(total_rev, 2),
        })

    return pd.DataFrame(rows)


pess_df = build_scenario("Pessimistic", sub_multiplier_from_m3=1.0,  conv_rate_m6=0.30, conv_rate_m12=0.50)
opt_df  = build_scenario("Optimistic",  sub_multiplier_from_m3=2.5,  conv_rate_m6=0.50, conv_rate_m12=0.75)


def find_breakeven(df):
    """Return first month where cumulative net community turns positive, else None."""
    cumulative = 0
    for _, row in df.iterrows():
        cumulative += row["Net community"]
        if cumulative >= 0:
            return int(row["Month"])
    return None


with tab5:
    st.markdown('<div class="section-title">Scenario assumptions</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="highlight-box">
    <b>Fixed across both scenarios</b><br>
    SEO baseline: $100,000/month · Active member retention: 10% of all subscribers ·
    LTV per depositor: $375 over 6 months ($62.50/month) ·
    Earn cap: $100/user/month · Weighted avg loyalty payout: $27.60/active user/month<br><br>
    <b>⚠️ Withdrawal minimum note:</b> The $100 minimum means casual users (~36% of active members,
    earning $15/month) take ~7 months to reach their first payout. This creates a disengagement risk
    in months 3–6 before they see any cash. Consider lower-threshold bonus redemptions in a later stage.
    </div>
    """, unsafe_allow_html=True)

    col_p, col_o = st.columns(2)
    with col_p:
        st.markdown("""
        <div style="background:#1a1320;border:1px solid #3d1f4e;border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.7rem;letter-spacing:0.15em;color:#c084fc;margin-bottom:0.5rem">
        ▼ PESSIMISTIC</div>
        <div style="font-size:0.85rem;color:#9ca3af;line-height:1.7">
        · ~285 new subscribers/month throughout<br>
        · No viral/partner boost<br>
        · 30% of active members convert by month 6<br>
        · 50% of active members convert by month 12
        </div></div>
        """, unsafe_allow_html=True)
    with col_o:
        st.markdown("""
        <div style="background:#13201a;border:1px solid #1f4e30;border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.7rem;letter-spacing:0.15em;color:#7ee8a2;margin-bottom:0.5rem">
        ▲ OPTIMISTIC</div>
        <div style="font-size:0.85rem;color:#9ca3af;line-height:1.7">
        · 285/month rising to ~715/month from month 3 (2.5× boost)<br>
        · Forum/partner/word-of-mouth effect<br>
        · 50% of active members convert by month 6<br>
        · 75% of active members convert by month 12
        </div></div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── KPI comparison: months 7–12 window ──────────────────────────────────
    st.markdown('<div class="section-title">Months 7–12 summary</div>', unsafe_allow_html=True)

    def window_kpis(df):
        w = df[df["Month"] >= 7]
        return {
            "active_m12":     int(df.iloc[-1]["Active members"]),
            "comm_rev_total":  w["Community revenue"].sum(),
            "loyalty_total":   w["Loyalty cost"].sum(),
            "net_comm_total":  w["Net community"].sum(),
            "total_rev_avg":   w["Total revenue"].mean(),
            "depositors_total": w["New depositors"].sum(),
        }

    pk = window_kpis(pess_df)
    ok = window_kpis(opt_df)

    col1, col2, col3 = st.columns(3)

    def comparison_kpi(col, label, pval, oval, fmt="$"):
        if fmt == "$":
            ps = f"${pval:,.0f}"
            os = f"${oval:,.0f}"
        else:
            ps = f"{pval:,.0f}"
            os = f"{oval:,.0f}"
        col.markdown(f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div style="display:flex;gap:1.5rem;margin-top:0.4rem;align-items:baseline">
                <div>
                    <div style="font-size:0.65rem;color:#c084fc;font-family:'Space Mono',monospace;letter-spacing:0.1em">PESS</div>
                    <div style="font-size:1.4rem;font-weight:700;font-family:'Space Mono',monospace;color:#c084fc">{ps}</div>
                </div>
                <div>
                    <div style="font-size:0.65rem;color:#7ee8a2;font-family:'Space Mono',monospace;letter-spacing:0.1em">OPT</div>
                    <div style="font-size:1.4rem;font-weight:700;font-family:'Space Mono',monospace;color:#7ee8a2">{os}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    comparison_kpi(col1, "Active members (mo. 12)", pk["active_m12"],     ok["active_m12"],     fmt="n")
    comparison_kpi(col2, "Community revenue (mo. 7–12)", pk["comm_rev_total"],  ok["comm_rev_total"])
    comparison_kpi(col3, "Loyalty costs (mo. 7–12)",     pk["loyalty_total"],   ok["loyalty_total"])

    col4, col5, col6 = st.columns(3)
    comparison_kpi(col4, "Net community (mo. 7–12)",  pk["net_comm_total"],  ok["net_comm_total"])
    comparison_kpi(col5, "Avg total revenue/month",   pk["total_rev_avg"],   ok["total_rev_avg"])
    comparison_kpi(col6, "New depositors (mo. 7–12)", pk["depositors_total"],ok["depositors_total"], fmt="n")

    st.markdown("---")

    # ── Chart 1: Community revenue vs loyalty cost ───────────────────────────
    st.markdown('<div class="section-title">Community revenue vs. loyalty cost</div>', unsafe_allow_html=True)
    fig_sc1 = go.Figure()
    fig_sc1.add_trace(go.Scatter(x=pess_df["Month"], y=pess_df["Community revenue"],
                                 name="Community rev (pessimistic)", line=dict(color="#c084fc", width=2, dash="dot")))
    fig_sc1.add_trace(go.Scatter(x=opt_df["Month"],  y=opt_df["Community revenue"],
                                 name="Community rev (optimistic)",  line=dict(color="#7ee8a2", width=2.5)))
    fig_sc1.add_trace(go.Scatter(x=pess_df["Month"], y=pess_df["Loyalty cost"],
                                 name="Loyalty cost (pessimistic)",  line=dict(color="#f59e0b", width=2, dash="dot")))
    fig_sc1.add_trace(go.Scatter(x=opt_df["Month"],  y=opt_df["Loyalty cost"],
                                 name="Loyalty cost (optimistic)",   line=dict(color="#ef4444", width=2)))
    fig_sc1.add_vrect(x0=6.5, x1=12.5, fillcolor="rgba(126,232,162,0.04)",
                      line_width=0, annotation_text="months 7–12", annotation_position="top left",
                      annotation_font_color="#4b5563")
    fig_sc1.update_layout(**BASE_LAYOUT, height=320,
                          xaxis=dict(**AXIS, title="Month", dtick=1),
                          yaxis=dict(**AXIS, title="USD / month"))
    st.plotly_chart(fig_sc1, use_container_width=True)

    # ── Chart 2: Net community P&L ───────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="section-title">Net community P&L (cumulative)</div>', unsafe_allow_html=True)
        fig_sc2 = go.Figure()
        fig_sc2.add_trace(go.Scatter(
            x=pess_df["Month"], y=pess_df["Net community"].cumsum(),
            name="Pessimistic", line=dict(color="#c084fc", width=2, dash="dot"),
            fill="tozeroy", fillcolor="rgba(192,132,252,0.06)"
        ))
        fig_sc2.add_trace(go.Scatter(
            x=opt_df["Month"], y=opt_df["Net community"].cumsum(),
            name="Optimistic", line=dict(color="#7ee8a2", width=2.5),
            fill="tozeroy", fillcolor="rgba(126,232,162,0.06)"
        ))
        fig_sc2.add_hline(y=0, line_dash="dash", line_color="#4b5563",
                          annotation_text="Break-even", annotation_font_color="#6b7280")
        fig_sc2.update_layout(**BASE_LAYOUT, height=300,
                              xaxis=dict(**AXIS, title="Month", dtick=1),
                              yaxis=dict(**AXIS, title="Cumulative net USD"))
        st.plotly_chart(fig_sc2, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Active members & new depositors</div>', unsafe_allow_html=True)
        fig_sc3 = go.Figure()
        fig_sc3.add_trace(go.Scatter(x=pess_df["Month"], y=pess_df["Active members"],
                                     name="Active members (pess)", line=dict(color="#c084fc", width=2, dash="dot")))
        fig_sc3.add_trace(go.Scatter(x=opt_df["Month"],  y=opt_df["Active members"],
                                     name="Active members (opt)",  line=dict(color="#7ee8a2", width=2.5)))
        fig_sc3.add_trace(go.Bar(x=pess_df["Month"], y=pess_df["New depositors"],
                                 name="New depositors (pess)", marker_color="#4a2d6e",
                                 marker_line_width=0, opacity=0.7, yaxis="y2"))
        fig_sc3.add_trace(go.Bar(x=opt_df["Month"],  y=opt_df["New depositors"],
                                 name="New depositors (opt)",  marker_color="#1a4e30",
                                 marker_line_width=0, opacity=0.7, yaxis="y2"))
        fig_sc3.update_layout(
            **BASE_LAYOUT, barmode="group", height=300,
            xaxis=dict(**AXIS, title="Month", dtick=1),
            yaxis=dict( **AXIS, title="Active members"),
            yaxis2=dict(overlaying="y", side="right", title="New depositors/month",
                        gridcolor="#1f2030", linecolor="#1f2030", showgrid=False),
        )
        st.plotly_chart(fig_sc3, use_container_width=True)

    # ── Full P&L tables ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">Full 12-month P&L tables</div>', unsafe_allow_html=True)

    tab_pess, tab_opt = st.tabs(["  ▼ Pessimistic  ", "  ▲ Optimistic  "])

    def format_pl_table(df):
        d = df.copy()
        for c in ["Community revenue", "Loyalty cost", "Net community", "SEO revenue", "Total revenue"]:
            d[c] = d[c].apply(lambda x: f"${x:,.0f}")
        for c in ["New subscribers", "Total subscribers", "Active members", "New depositors"]:
            d[c] = d[c].apply(lambda x: f"{x:,}")
        return d

    with tab_pess:
        be = find_breakeven(pess_df)
        if be:
            st.markdown(f'<div class="highlight-box">Community P&L turns cumulatively positive at <b>month {be}</b>.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="highlight-box">⚠️ Community P&L does not break even within 12 months in this scenario.</div>', unsafe_allow_html=True)
        st.dataframe(format_pl_table(pess_df), use_container_width=True, hide_index=True)

    with tab_opt:
        be = find_breakeven(opt_df)
        if be:
            st.markdown(f'<div class="highlight-box">Community P&L turns cumulatively positive at <b>month {be}</b>.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="highlight-box">⚠️ Community P&L does not break even within 12 months in this scenario.</div>', unsafe_allow_html=True)
        st.dataframe(format_pl_table(opt_df), use_container_width=True, hide_index=True)