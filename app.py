import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import os
import sqlite3

st.set_page_config(
    page_title="Customer Shopping Behavior Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-card h3 {
        font-size: 0.85rem;
        color: #64748b;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card p {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin: 6px 0 0 0;
    }
    .metric-card .caption {
        font-size: 0.75rem;
        color: #10b981;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_CSV = os.path.join(BASE_DIR, "customer_shopping_behavior_cleaned.csv")
RAW_CSV = os.path.join(BASE_DIR, "customer_shopping_behavior.csv")
SQLITE_DB = os.path.join(BASE_DIR, "customer_behavior.db")
DUCKDB_DB = os.path.join(BASE_DIR, "customer_behavior.duckdb")

@st.cache_data
def load_data():
    if os.path.exists(CLEANED_CSV):
        df = pd.read_csv(CLEANED_CSV)
    elif os.path.exists(RAW_CSV):
        # Clean on the fly
        df = pd.read_csv(RAW_CSV)
        df['Review Rating'] = df.groupby('Category')['Review Rating'].transform(lambda x: x.fillna(x.median()))
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        df = df.rename(columns={'purchase_amount_(usd)': 'purchase_amount'})
        labels = ['Young Adult', 'Adult', 'Middle-aged', 'Senior']
        df['age_group'] = pd.qcut(df['age'], q=4, labels=labels)
        frequency_mapping = {
            'Fortnightly': 14, 'Weekly': 7, 'Monthly': 30, 'Quarterly': 90,
            'Bi-Weekly': 14, 'Annually': 365, 'Every 3 Months': 90
        }
        df['purchase_frequency_days'] = df['frequency_of_purchases'].map(frequency_mapping)
        if 'promo_code_used' in df.columns:
            df = df.drop(columns=['promo_code_used'])
    else:
        st.error("Dataset not found. Please ensure customer_shopping_behavior.csv is in the project root.")
        st.stop()
    return df

df_full = load_data()

# ----------------- SIDEBAR FILTERS (POWER BI SLICERS) -----------------
st.sidebar.image("https://img.icons8.com/isometric/100/combo-chart.png", width=60)
st.sidebar.title("Dashboard Slicers")
st.sidebar.markdown("Filter all visuals across the report:")

# Slicer 1: Subscription Status
all_subs = sorted(df_full['subscription_status'].unique().tolist())
sub_filter = st.sidebar.multiselect("Subscription Status", options=all_subs, default=all_subs)

# Slicer 2: Gender
all_genders = sorted(df_full['gender'].unique().tolist())
gender_filter = st.sidebar.multiselect("Gender", options=all_genders, default=all_genders)

# Slicer 3: Category
all_cats = sorted(df_full['category'].unique().tolist())
cat_filter = st.sidebar.multiselect("Product Category", options=all_cats, default=all_cats)

# Slicer 4: Shipping Type
all_shipping = sorted(df_full['shipping_type'].unique().tolist())
shipping_filter = st.sidebar.multiselect("Shipping Type", options=all_shipping, default=all_shipping)

# Slicer 5: Age Group
all_age_groups = sorted(df_full['age_group'].dropna().unique().tolist())
age_filter = st.sidebar.multiselect("Age Group", options=all_age_groups, default=all_age_groups)

# Slicer 6: Season
all_seasons = sorted(df_full['season'].unique().tolist())
season_filter = st.sidebar.multiselect("Season", options=all_seasons, default=all_seasons)

# Apply filters
df = df_full[
    (df_full['subscription_status'].isin(sub_filter)) &
    (df_full['gender'].isin(gender_filter)) &
    (df_full['category'].isin(cat_filter)) &
    (df_full['shipping_type'].isin(shipping_filter)) &
    (df_full['age_group'].isin(age_filter)) &
    (df_full['season'].isin(season_filter))
]

st.sidebar.markdown("---")
st.sidebar.info(f"Showing **{len(df):,}** of **{len(df_full):,}** records ({len(df)/len(df_full)*100:.1f}%)")

# Reset button
if st.sidebar.button("Reset Filters"):
    st.rerun()

# ----------------- HEADER -----------------
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown('<div class="main-title">🛍️ Customer Shopping Behavior Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">End-to-End Retail Data Analysis: Python · SQL (DuckDB/SQLite) · Interactive Dashboard</div>', unsafe_allow_html=True)
with col_badge:
    st.markdown("""
        <div style="background-color: #e0f2fe; border: 1px solid #7dd3fc; border-radius: 8px; padding: 10px; text-align: center; margin-top: 10px;">
            <span style="color: #0369a1; font-weight: 600; font-size: 0.85rem;"> macOS Power BI Alternative</span>
        </div>
    """, unsafe_allow_html=True)

# ----------------- TABS -----------------
tab_dash, tab_sql, tab_data, tab_report = st.tabs([
    "📊 Power BI Dashboard",
    "🔍 SQL Business Questions",
    "📋 Data Explorer",
    "📑 Executive Report & Strategy"
])

# ================= TAB 1: DASHBOARD =================
with tab_dash:
    if len(df) == 0:
        st.warning("No records match the current filter selection. Please adjust your filters.")
    else:
        # Top KPI Cards
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Number of Customers</h3>
                    <p>{len(df):,}</p>
                    <div class="caption">{len(df)/len(df_full)*100:.1f}% of cohort</div>
                </div>
            """, unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Total Revenue</h3>
                    <p>${df['purchase_amount'].sum():,.2f}</p>
                    <div class="caption">Avg ${(df['purchase_amount'].sum()/len(df)):.2f}/cust</div>
                </div>
            """, unsafe_allow_html=True)
        with kpi3:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Average Purchase Amount</h3>
                    <p>${df['purchase_amount'].mean():.2f}</p>
                    <div class="caption">Std: ${df['purchase_amount'].std():.2f}</div>
                </div>
            """, unsafe_allow_html=True)
        with kpi4:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Average Review Rating</h3>
                    <p>{df['review_rating'].mean():.2f} ★</p>
                    <div class="caption">Scale 1.0 – 5.0</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 1: Donut Chart (Subscription) & Clustered Column (Revenue by Category)
        r1_c1, r1_c2 = st.columns([1, 1.3])
        with r1_c1:
            st.subheader("Subscription Status Distribution")
            sub_counts = df['subscription_status'].value_counts().reset_index()
            sub_counts.columns = ['subscription_status', 'count']
            fig_sub = px.pie(
                sub_counts,
                names='subscription_status',
                values='count',
                hole=0.55,
                color='subscription_status',
                color_discrete_map={'Yes': '#3b82f6', 'No': '#94a3b8'}
            )
            fig_sub.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_sub, use_container_width=True)

        with r1_c2:
            st.subheader("Total Revenue by Product Category")
            cat_rev = df.groupby('category')['purchase_amount'].sum().reset_index()
            cat_rev = cat_rev.sort_values(by='purchase_amount', ascending=False)
            fig_cat_rev = px.bar(
                cat_rev,
                x='category',
                y='purchase_amount',
                text_auto='.2s',
                color='category',
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_cat_rev.update_layout(
                showlegend=False,
                xaxis_title="Category",
                yaxis_title="Total Revenue (USD)",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_cat_rev, use_container_width=True)

        # Row 2: Customer Orders by Category & Revenue by Age Group
        r2_c1, r2_c2 = st.columns([1, 1])
        with r2_c1:
            st.subheader("Customer Orders by Category")
            cat_cnt = df.groupby('category')['customer_id'].count().reset_index()
            cat_cnt = cat_cnt.sort_values(by='customer_id', ascending=False)
            fig_cat_cnt = px.bar(
                cat_cnt,
                x='category',
                y='customer_id',
                text_auto=True,
                color='category',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_cat_cnt.update_layout(
                showlegend=False,
                xaxis_title="Category",
                yaxis_title="Total Orders",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_cat_cnt, use_container_width=True)

        with r2_c2:
            st.subheader("Total Revenue by Age Group")
            age_rev = df.groupby('age_group', observed=False)['purchase_amount'].sum().reset_index()
            age_rev = age_rev.sort_values(by='purchase_amount', ascending=False)
            fig_age_rev = px.bar(
                age_rev,
                y='age_group',
                x='purchase_amount',
                orientation='h',
                text_auto='.2s',
                color='age_group',
                color_discrete_sequence=['#f59e0b', '#10b981', '#3b82f6', '#8b5cf6']
            )
            fig_age_rev.update_layout(
                showlegend=False,
                yaxis_title="Age Group",
                xaxis_title="Total Revenue (USD)",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_age_rev, use_container_width=True)

        # Row 3: Customer Orders by Age Group & Customer Segmentation
        r3_c1, r3_c2 = st.columns([1, 1])
        with r3_c1:
            st.subheader("Customer Count by Age Group")
            age_cnt = df.groupby('age_group', observed=False)['customer_id'].count().reset_index()
            fig_age_cnt = px.bar(
                age_cnt,
                y='age_group',
                x='customer_id',
                orientation='h',
                text_auto=True,
                color='age_group',
                color_discrete_sequence=['#06b6d4', '#ec4899', '#6366f1', '#14b8a6']
            )
            fig_age_cnt.update_layout(
                showlegend=False,
                yaxis_title="Age Group",
                xaxis_title="Customer Count",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_age_cnt, use_container_width=True)

        with r3_c2:
            st.subheader("Customer Segmentation (Loyalty)")
            def seg_label(p):
                if p == 1:
                    return 'New'
                elif 2 <= p <= 10:
                    return 'Returning'
                else:
                    return 'Loyal'
            df_seg = df.copy()
            df_seg['segment'] = df_seg['previous_purchases'].apply(seg_label)
            seg_summary = df_seg['segment'].value_counts().reset_index()
            seg_summary.columns = ['segment', 'count']
            fig_seg = px.pie(
                seg_summary,
                names='segment',
                values='count',
                color='segment',
                color_discrete_map={'Loyal': '#10b981', 'Returning': '#f59e0b', 'New': '#3b82f6'}
            )
            fig_seg.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_seg, use_container_width=True)

        # Row 4: Shipping Impact & Top Rated Products
        r4_c1, r4_c2 = st.columns([1, 1])
        with r4_c1:
            st.subheader("Average Purchase by Shipping Type")
            ship_summary = df.groupby('shipping_type')['purchase_amount'].agg(['mean', 'count']).reset_index()
            ship_summary.columns = ['shipping_type', 'avg_spend', 'count']
            ship_summary = ship_summary.sort_values(by='avg_spend', ascending=False)
            fig_ship = px.bar(
                ship_summary,
                x='shipping_type',
                y='avg_spend',
                text_auto='.2f',
                color='shipping_type',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_ship.update_layout(
                showlegend=False,
                xaxis_title="Shipping Type",
                yaxis_title="Average Spend (USD)",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_ship, use_container_width=True)

        with r4_c2:
            st.subheader("Top 5 Products by Rating")
            top_rated = df.groupby('item_purchased')['review_rating'].agg(['mean', 'count']).reset_index()
            top_rated.columns = ['item_purchased', 'avg_rating', 'count']
            top_5 = top_rated.sort_values(by='avg_rating', ascending=False).head(5)
            fig_top = px.bar(
                top_5,
                x='item_purchased',
                y='avg_rating',
                text_auto='.2f',
                color='avg_rating',
                color_continuous_scale='Viridis'
            )
            fig_top.update_layout(
                xaxis_title="Product",
                yaxis_title="Average Rating",
                coloraxis_showscale=False,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_top, use_container_width=True)


# ================= TAB 2: SQL BUSINESS QUESTIONS =================
with tab_sql:
    st.subheader("Interactive SQL Engine & Business Analytics")
    st.markdown("All 10 business questions from the project portfolio are executable live using DuckDB / SQLite:")

    questions = {
        "Q1: Revenue by Gender": {
            "sql": "SELECT gender, SUM(purchase_amount) AS revenue, ROUND(100.0 * SUM(purchase_amount) / (SELECT SUM(purchase_amount) FROM customer), 2) AS revenue_share_pct FROM customer GROUP BY gender ORDER BY revenue DESC;",
            "description": "Calculates total revenue generated by male vs. female customers.",
            "insight": "Male customers generate 67.7% of total revenue ($157.9K), while female customers generate 32.3% ($75.2K)."
        },
        "Q2: High-Spending Discount Users": {
            "sql": "SELECT customer_id, purchase_amount, category, item_purchased FROM customer WHERE discount_applied = 'Yes' AND purchase_amount >= (SELECT AVG(purchase_amount) FROM customer) LIMIT 15;",
            "description": "Customers who used a discount but still spent at or above the average purchase amount ($59.76).",
            "insight": "839 shoppers maximized discount value while maintaining high cart sizes (averaging $79.79 per transaction)."
        },
        "Q3: Top 5 Products by Rating": {
            "sql": "SELECT item_purchased, ROUND(AVG(review_rating::numeric), 2) AS avg_rating, COUNT(*) AS total_reviews FROM customer GROUP BY item_purchased ORDER BY avg_rating DESC LIMIT 5;",
            "description": "Products with the highest average customer review rating.",
            "insight": "Gloves (3.86), Sandals (3.84), and Boots (3.82) are the highest-rated items."
        },
        "Q4: Standard vs Express Shipping Spend": {
            "sql": "SELECT shipping_type, ROUND(AVG(purchase_amount), 2) AS avg_purchase_amount, COUNT(*) AS total_orders FROM customer WHERE shipping_type IN ('Standard','Express') GROUP BY shipping_type;",
            "description": "Compares average purchase amounts between Standard and Express shipping.",
            "insight": "Express shipping customers spend an average of $60.48 vs $58.46 for Standard shipping (~3.5% premium)."
        },
        "Q5: Subscribed vs Non-Subscribed Spend": {
            "sql": "SELECT subscription_status, COUNT(customer_id) AS total_customers, ROUND(AVG(purchase_amount), 2) AS avg_spend, ROUND(SUM(purchase_amount), 2) AS total_revenue FROM customer GROUP BY subscription_status ORDER BY total_revenue DESC;",
            "description": "Do subscribed customers spend more? Compare average spend and total revenue.",
            "insight": "Subscribers account for 27% of customers ($62.6K revenue). Average spend is virtually identical (~$59.50 vs ~$59.87), indicating loyalty programs should focus on purchase frequency rather than basket size."
        },
        "Q6: Top 5 Discounted Products": {
            "sql": "SELECT item_purchased, ROUND(100.0 * SUM(CASE WHEN discount_applied = 'Yes' THEN 1 ELSE 0 END)/COUNT(*), 2) AS discount_rate, COUNT(*) AS total_purchases FROM customer GROUP BY item_purchased ORDER BY discount_rate DESC LIMIT 5;",
            "description": "Top 5 products with highest percentage of purchases with discounts applied.",
            "insight": "Hats (50%), Sneakers (49.7%), and Coats (49.1%) see roughly half of all sales driven by discounts."
        },
        "Q7: Customer Segmentation (New, Returning, Loyal)": {
            "sql": "WITH customer_type AS (SELECT customer_id, previous_purchases, CASE WHEN previous_purchases = 1 THEN 'New' WHEN previous_purchases BETWEEN 2 AND 10 THEN 'Returning' ELSE 'Loyal' END AS customer_segment FROM customer) SELECT customer_segment, COUNT(*) AS number_of_customers, ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer), 2) AS segment_pct FROM customer_type GROUP BY customer_segment ORDER BY number_of_customers DESC;",
            "description": "Segments customers based on previous purchases (1 = New, 2-10 = Returning, 11+ = Loyal).",
            "insight": "79.9% of shoppers are Loyal repeat customers (3,116 customers), demonstrating exceptional customer retention."
        },
        "Q8: Top 3 Products per Category": {
            "sql": "WITH item_counts AS (SELECT category, item_purchased, COUNT(customer_id) AS total_orders, ROW_NUMBER() OVER (PARTITION BY category ORDER BY COUNT(customer_id) DESC) AS item_rank FROM customer GROUP BY category, item_purchased) SELECT item_rank, category, item_purchased, total_orders FROM item_counts WHERE item_rank <= 3 ORDER BY category, item_rank;",
            "description": "Top 3 most purchased items within each retail category.",
            "insight": "Clothing is led by Blouses and Pants (171 each), Accessories by Jewelry (171), Outerwear by Jackets (163)."
        },
        "Q9: Repeat Buyers Subscription Rate": {
            "sql": "SELECT subscription_status, COUNT(customer_id) AS repeat_buyers, ROUND(100.0 * COUNT(customer_id) / SUM(COUNT(customer_id)) OVER(), 2) AS pct_of_repeat_buyers FROM customer WHERE previous_purchases > 5 GROUP BY subscription_status;",
            "description": "Are repeat buyers (>5 previous purchases) also likely to subscribe?",
            "insight": "72.4% (2,518) of repeat buyers are NOT subscribed, representing a massive organic conversion opportunity."
        },
        "Q10: Revenue Contribution by Age Group": {
            "sql": "SELECT age_group, COUNT(customer_id) AS customer_count, ROUND(AVG(purchase_amount), 2) AS avg_spend, SUM(purchase_amount) AS total_revenue, ROUND(100.0 * SUM(purchase_amount) / (SELECT SUM(purchase_amount) FROM customer), 2) AS revenue_share_pct FROM customer GROUP BY age_group ORDER BY total_revenue DESC;",
            "description": "Revenue and customer count contribution across demographic age brackets.",
            "insight": "Young Adults generate the highest revenue ($62.1K / 26.7%), closely followed by Middle-aged shoppers ($59.2K / 25.4%)."
        }
    }

    selected_q = st.selectbox("Select Business Question to Run:", list(questions.keys()))
    q_data = questions[selected_q]

    st.markdown(f"**Question Objective:** {q_data['description']}")

    col_q1, col_q2 = st.columns([1.2, 1])
    with col_q1:
        st.code(q_data['sql'], language="sql")
    with col_q2:
        st.info(f"💡 **Business Insight:**\n\n{q_data['insight']}")

    # Execute query using duckdb on df_full
    con = duckdb.connect()
    con.register('customer', df_full)
    res_df = con.execute(q_data['sql']).df()

    st.dataframe(res_df, use_container_width=True)

    st.markdown("---")
    st.subheader("⚡ Live SQL Playground")
    st.markdown("Write and execute any custom SQL query on the `customer` table:")
    default_custom_sql = "SELECT category, ROUND(AVG(purchase_amount), 2) as avg_price, COUNT(*) as orders FROM customer GROUP BY category ORDER BY avg_price DESC;"
    user_sql = st.text_area("Custom SQL Query:", value=default_custom_sql, height=90)
    if st.button("Execute Query"):
        try:
            custom_res = con.execute(user_sql).df()
            st.success(f"Returned {len(custom_res):,} rows")
            st.dataframe(custom_res, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Error: {e}")


# ================= TAB 3: DATA EXPLORER =================
with tab_data:
    st.subheader("Customer Shopping Behavior Dataset")
    st.markdown(f"Showing **{len(df):,}** records with current sidebar filters applied.")

    search_term = st.text_input("Quick Search (Item, Location, Color, Size):", "")
    display_df = df.copy()
    if search_term:
        mask = (
            display_df['item_purchased'].str.contains(search_term, case=False, na=False) |
            display_df['location'].str.contains(search_term, case=False, na=False) |
            display_df['color'].str.contains(search_term, case=False, na=False) |
            display_df['size'].str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[mask]

    st.dataframe(display_df, use_container_width=True, height=400)

    csv_data = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned Data as CSV",
        data=csv_data,
        file_name="customer_shopping_behavior_filtered.csv",
        mime="text/csv"
    )


# ================= TAB 4: EXECUTIVE REPORT =================
with tab_report:
    st.subheader("Executive Report & Strategic Business Recommendations")

    st.markdown("""
    ### 🎯 Project Context & Business Problem
    A leading retail organization sought to understand shopping patterns, revenue drivers, customer retention, and subscription adoption across 3,900 customer purchases across 50 US states. 
    The goal is to translate raw transactional data into actionable strategies that optimize customer lifetime value (LTV) and revenue growth.

    ---

    ### 📌 Key Analytical Findings

    1. **Male Customers Drive Primary Revenue Volume:**
       - Male customers generate **$157,890 (67.7%)** of revenue, compared to **$75,191 (32.3%)** from female shoppers.
       - *Actionable Takeaway:* Expand marketing efforts targeting male shopper categories while testing female-oriented campaigns to capture untapped market share.

    2. **Subscription Upsell Potential is High:**
       - Only **27% of customers (1,053)** are subscribers, yet repeat buyers (>5 purchases) number **3,476**, of which **2,518 (72.4%) are NOT subscribed**.
       - Average spend between subscribers ($59.49) and non-subscribers ($59.87) is nearly identical.
       - *Actionable Takeaway:* Subscribers shouldn't just be offered discounts; they need frequency-boosting perks like exclusive early product access, bundled shipping, and quarterly reward tiers.

    3. **Discount Sensitivity vs. High Spenders:**
       - **839 customers** used discounts but spent above the average purchase amount ($79.79 avg spend).
       - Items like Hats (50%), Sneakers (49.7%), and Coats (49.1%) have the highest discount rates.
       - *Actionable Takeaway:* Introduce minimum spend thresholds (e.g., "$15 off on purchases above $80") to protect margins while catering to high-spending discount shoppers.

    4. **Express Shipping Customers Spend More:**
       - Express shipping transactions average **$60.48**, compared to **$58.46** for Standard shipping.
       - *Actionable Takeaway:* Offer Express shipping upgrades for orders reaching $75+ to incentivize cart-size expansion.

    5. **Customer Retention is Strong:**
       - **79.9%** of customers are classified as Loyal (11+ prior purchases).
       - *Actionable Takeaway:* Implement a formal tiered loyalty club (Bronze, Silver, Gold) to maintain engagement and prevent churn to competitors.

    ---

    ### 🛠️ Architecture on macOS
    - **Data Cleaning & Wrangling:** Python 3.14 + Pandas
    - **SQL Query Engine:** DuckDB & SQLite (zero external server dependencies)
    - **Visual Analytics:** Streamlit + Plotly (Native Mac replacement for Power BI Desktop)
    - **Exportable Dashboard:** Standalone single-file HTML (`dashboard.html`)
    """)

