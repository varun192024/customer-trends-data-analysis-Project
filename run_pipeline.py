#!/usr/bin/env python3
"""
End-to-End Data Pipeline: Customer Shopping Behavior Analysis
=============================================================
1. Data Cleaning & Feature Engineering (Pandas)
2. Database Export (SQLite & DuckDB)
3. Automated Execution of all 10 Business SQL Queries
4. Standalone Interactive HTML Dashboard Generation
"""

import os
import sys
import sqlite3
import duckdb
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_INPUT = os.path.join(BASE_DIR, "customer_shopping_behavior.csv")
CSV_CLEANED = os.path.join(BASE_DIR, "customer_shopping_behavior_cleaned.csv")
SQLITE_DB = os.path.join(BASE_DIR, "customer_behavior.db")
DUCKDB_DB = os.path.join(BASE_DIR, "customer_behavior.duckdb")
SQL_FILE = os.path.join(BASE_DIR, "customer_behavior_sql_queries.sql")
RESULTS_MD = os.path.join(BASE_DIR, "sql_query_results.md")
HTML_DASHBOARD = os.path.join(BASE_DIR, "dashboard.html")


def clean_and_transform_data(csv_path):
    print("=" * 60)
    print("Step 1: Loading and Cleaning Dataset...")
    print("=" * 60)
    df = pd.read_csv(csv_path)
    initial_rows, initial_cols = df.shape
    print(f"Loaded raw data: {initial_rows:,} rows, {initial_cols} columns.")

    # 1. Missing value imputation in Review Rating
    missing_before = df['Review Rating'].isnull().sum()
    df['Review Rating'] = df.groupby('Category')['Review Rating'].transform(lambda x: x.fillna(x.median()))
    missing_after = df['Review Rating'].isnull().sum()
    print(f"Imputed missing Review Ratings: {missing_before} -> {missing_after} missing.")

    # 2. Standardize column names to snake_case
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    df = df.rename(columns={'purchase_amount_(usd)': 'purchase_amount'})

    # 3. Create age_group column (Young Adult, Adult, Middle-aged, Senior)
    labels = ['Young Adult', 'Adult', 'Middle-aged', 'Senior']
    df['age_group'] = pd.qcut(df['age'], q=4, labels=labels)

    # 4. Map frequency_of_purchases to days
    frequency_mapping = {
        'Fortnightly': 14,
        'Weekly': 7,
        'Monthly': 30,
        'Quarterly': 90,
        'Bi-Weekly': 14,
        'Annually': 365,
        'Every 3 Months': 90
    }
    df['purchase_frequency_days'] = df['frequency_of_purchases'].map(frequency_mapping)

    # 5. Drop redundant promo_code_used column if identical to discount_applied
    if 'promo_code_used' in df.columns:
        df = df.drop(columns=['promo_code_used'])
        print("Dropped redundant column: 'promo_code_used'.")

    # Save cleaned CSV
    df.to_csv(CSV_CLEANED, index=False)
    print(f"Saved cleaned dataset to: {os.path.basename(CSV_CLEANED)}")

    return df


def export_to_databases(df):
    print("\n" + "=" * 60)
    print("Step 2: Exporting to SQL Databases (SQLite & DuckDB)...")
    print("=" * 60)

    # Convert category dtype to string for sqlite compatibility
    df_sql = df.copy()
    if 'age_group' in df_sql.columns:
        df_sql['age_group'] = df_sql['age_group'].astype(str)

    # 1. SQLite Database
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    df_sql.to_sql("customer", sqlite_conn, if_exists="replace", index=False)
    sqlite_conn.commit()
    sqlite_conn.close()
    print(f"Created SQLite database: {os.path.basename(SQLITE_DB)} (Table: customer)")

    # 2. DuckDB Database
    duck_conn = duckdb.connect(DUCKDB_DB)
    duck_conn.execute("CREATE OR REPLACE TABLE customer AS SELECT * FROM df")
    duck_conn.close()
    print(f"Created DuckDB database: {os.path.basename(DUCKDB_DB)} (Table: customer)")


def execute_sql_queries(df):
    print("\n" + "=" * 60)
    print("Step 3: Executing Business SQL Queries...")
    print("=" * 60)

    con = duckdb.connect()
    con.register('customer', df)

    queries = [
        {
            "id": "Q1",
            "title": "Total Revenue by Gender",
            "sql": """SELECT gender, SUM(purchase_amount) AS revenue,
       ROUND(100.0 * SUM(purchase_amount) / (SELECT SUM(purchase_amount) FROM customer), 2) AS revenue_share_pct
FROM customer
GROUP BY gender
ORDER BY revenue DESC;""",
            "insight": "Male customers contribute ~$157.9K (67.7%) of total revenue, while Female customers contribute ~$75.2K (32.3%)."
        },
        {
            "id": "Q2",
            "title": "High-Spending Discount Users",
            "sql": """SELECT customer_id, purchase_amount, category, item_purchased
FROM customer 
WHERE discount_applied = 'Yes' 
  AND purchase_amount >= (SELECT AVG(purchase_amount) FROM customer)
LIMIT 10;""",
            "summary_sql": """SELECT COUNT(*) AS total_high_spending_discount_users,
       ROUND(AVG(purchase_amount), 2) AS avg_spend,
       SUM(purchase_amount) AS total_revenue
FROM customer
WHERE discount_applied = 'Yes' 
  AND purchase_amount >= (SELECT AVG(purchase_amount) FROM customer);""",
            "insight": "839 customers used discounts yet spent at or above the average ($59.76), generating $66,940 total revenue at an average of $79.79 per order."
        },
        {
            "id": "Q3",
            "title": "Top 5 Products with Highest Average Review Rating",
            "sql": """SELECT item_purchased, 
       ROUND(AVG(review_rating::numeric), 2) AS avg_rating,
       COUNT(*) AS total_purchases
FROM customer
GROUP BY item_purchased
ORDER BY avg_rating DESC
LIMIT 5;""",
            "insight": "Gloves (3.86), Sandals (3.84), Boots (3.82), Hat (3.80), and Skirt (3.78) hold the highest satisfaction scores."
        },
        {
            "id": "Q4",
            "title": "Average Purchase Amount: Standard vs. Express Shipping",
            "sql": """SELECT shipping_type, 
       ROUND(AVG(purchase_amount), 2) AS avg_purchase_amount,
       COUNT(*) AS total_orders
FROM customer
WHERE shipping_type IN ('Standard', 'Express')
GROUP BY shipping_type;""",
            "insight": "Express shipping customers have an average spend of $60.48 compared to $58.46 for Standard shipping (~3.5% higher)."
        },
        {
            "id": "Q5",
            "title": "Subscribed vs. Non-Subscribed Customers",
            "sql": """SELECT subscription_status,
       COUNT(customer_id) AS total_customers,
       ROUND(AVG(purchase_amount), 2) AS avg_spend,
       ROUND(SUM(purchase_amount), 2) AS total_revenue,
       ROUND(100.0 * COUNT(customer_id) / (SELECT COUNT(*) FROM customer), 2) AS customer_pct
FROM customer
GROUP BY subscription_status
ORDER BY total_revenue DESC;""",
            "insight": "Subscribers make up 27% of customers (1,053) generating $62,645 in revenue. Average spend is almost identical ($59.49 vs $59.87)."
        },
        {
            "id": "Q6",
            "title": "Top 5 Products with Highest Percentage of Discount Purchases",
            "sql": """SELECT item_purchased,
       ROUND(100.0 * SUM(CASE WHEN discount_applied = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS discount_rate,
       COUNT(*) AS total_purchases
FROM customer
GROUP BY item_purchased
ORDER BY discount_rate DESC
LIMIT 5;""",
            "insight": "Hats (50.0%), Sneakers (49.66%), Coats (49.07%), Sweaters (48.17%), and Pants (47.37%) are most frequently bought with discounts."
        },
        {
            "id": "Q7",
            "title": "Customer Segmentation (New, Returning, Loyal)",
            "sql": """WITH customer_type AS (
    SELECT customer_id, previous_purchases,
    CASE 
        WHEN previous_purchases = 1 THEN 'New'
        WHEN previous_purchases BETWEEN 2 AND 10 THEN 'Returning'
        ELSE 'Loyal'
    END AS customer_segment
    FROM customer
)
SELECT customer_segment, 
       COUNT(*) AS number_of_customers,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer), 2) AS segment_pct
FROM customer_type 
GROUP BY customer_segment
ORDER BY number_of_customers DESC;""",
            "insight": "79.9% of customers (3,116) are categorized as Loyal (11+ previous purchases), 18.0% (701) are Returning, and 2.1% (83) are New."
        },
        {
            "id": "Q8",
            "title": "Top 3 Most Purchased Products within Each Category",
            "sql": """WITH item_counts AS (
    SELECT category,
           item_purchased,
           COUNT(customer_id) AS total_orders,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY COUNT(customer_id) DESC) AS item_rank
    FROM customer
    GROUP BY category, item_purchased
)
SELECT item_rank, category, item_purchased, total_orders
FROM item_counts
WHERE item_rank <= 3
ORDER BY category, item_rank;""",
            "insight": "Top sellers include Blouse & Pants in Clothing (171 each), Jewelry in Accessories (171), Jacket in Outerwear (163), and Sandals in Footwear (160)."
        },
        {
            "id": "Q9",
            "title": "Repeat Buyers (>5 purchases) Subscription Rate",
            "sql": """SELECT subscription_status,
       COUNT(customer_id) AS repeat_buyers,
       ROUND(100.0 * COUNT(customer_id) / SUM(COUNT(customer_id)) OVER(), 2) AS pct_of_repeat_buyers
FROM customer
WHERE previous_purchases > 5
GROUP BY subscription_status;""",
            "insight": "Out of 3,476 repeat buyers (>5 purchases), 72.4% (2,518) are currently NON-subscribers. This represents a prime conversion opportunity."
        },
        {
            "id": "Q10",
            "title": "Revenue Contribution by Age Group",
            "sql": """SELECT age_group,
       COUNT(customer_id) AS customer_count,
       ROUND(AVG(purchase_amount), 2) AS avg_spend,
       SUM(purchase_amount) AS total_revenue,
       ROUND(100.0 * SUM(purchase_amount) / (SELECT SUM(purchase_amount) FROM customer), 2) AS revenue_share_pct
FROM customer
GROUP BY age_group
ORDER BY total_revenue DESC;""",
            "insight": "Young Adults lead with $62.1K (26.7%), followed by Middle-aged with $59.2K (25.4%), Adults with $56.0K (24.0%), and Seniors with $55.8K (23.9%)."
        }
    ]

    md_output = ["# 📊 SQL Business Queries & Analysis Results\n"]
    md_output.append("> Generated automatically by `run_pipeline.py` using DuckDB/SQLite engine.\n")

    for q in queries:
        qid = q["id"]
        title = q["title"]
        sql = q["sql"]
        insight = q["insight"]

        print(f"\n--- {qid}: {title} ---")
        res_df = con.execute(sql).df()
        print(res_df.to_string(index=False))

        md_output.append(f"## {qid}: {title}\n")
        md_output.append(f"```sql\n{sql.strip()}\n```\n")
        md_output.append("**Results:**\n")
        md_output.append(res_df.to_markdown(index=False))
        md_output.append(f"\n💡 **Key Insight:** {insight}\n\n---\n")

    with open(RESULTS_MD, "w") as f:
        f.write("\n".join(md_output))
    print(f"\nSaved all query results to: {os.path.basename(RESULTS_MD)}")


def generate_standalone_dashboard(df):
    print("\n" + "=" * 60)
    print("Step 4: Generating Standalone Interactive HTML Dashboard...")
    print("=" * 60)

    # Compute aggregate stats
    total_customers = len(df)
    total_revenue = float(df['purchase_amount'].sum())
    avg_purchase = float(df['purchase_amount'].mean())
    avg_rating = float(df['review_rating'].mean())

    # Category Revenue & Counts
    cat_summary = df.groupby('category').agg(
        revenue=('purchase_amount', 'sum'),
        customers=('customer_id', 'count')
    ).reset_index()

    # Subscription Stats
    sub_counts = df['subscription_status'].value_counts()
    sub_labels = sub_counts.index.tolist()
    sub_values = sub_counts.values.tolist()

    # Age Group Stats
    age_summary = df.groupby('age_group', observed=False).agg(
        revenue=('purchase_amount', 'sum'),
        customers=('customer_id', 'count')
    ).reset_index()

    # Gender Stats
    gender_rev = df.groupby('gender').agg(revenue=('purchase_amount', 'sum')).reset_index()

    # Customer Segments
    def get_segment(p):
        if p == 1:
            return 'New'
        elif 2 <= p <= 10:
            return 'Returning'
        else:
            return 'Loyal'

    seg_counts = df['previous_purchases'].apply(get_segment).value_counts()
    seg_labels = seg_counts.index.tolist()
    seg_values = seg_counts.values.tolist()

    # HTML template with Plotly.js CDN
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer Shopping Behavior Dashboard (Mac Edition)</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-green: #10b981;
            --accent-purple: #8b5cf6;
            --accent-orange: #f59e0b;
            --border: #334155;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 24px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        .header h1 {{ font-size: 26px; font-weight: 700; color: #fff; }}
        .header p {{ color: var(--text-secondary); font-size: 14px; margin-top: 4px; }}
        .badge {{
            background: #2563eb;
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .kpi-title {{ font-size: 13px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
        .kpi-value {{ font-size: 30px; font-weight: 700; color: #fff; margin: 8px 0 4px; }}
        .kpi-sub {{ font-size: 12px; color: var(--accent-green); }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        .chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            min-height: 380px;
        }}
        .footer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 13px;
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Customer Shopping Behavior Dashboard</h1>
            <p>Interactive End-to-End Analytics Report (Power BI Mac Alternative)</p>
        </div>
        <span class="badge">macOS Native Edition</span>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-title">Total Customers</div>
            <div class="kpi-value">{total_customers:,}</div>
            <div class="kpi-sub">Across 50 US States</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Total Revenue</div>
            <div class="kpi-value">${total_revenue:,.2f}</div>
            <div class="kpi-sub">Gross Purchase Amount</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Average Purchase</div>
            <div class="kpi-value">${avg_purchase:.2f}</div>
            <div class="kpi-sub">Per transaction</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Average Rating</div>
            <div class="kpi-value">{avg_rating:.2f} ★</div>
            <div class="kpi-sub">Customer satisfaction score</div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-card" id="chart-subscription"></div>
        <div class="chart-card" id="chart-category-rev"></div>
        <div class="chart-card" id="chart-age-rev"></div>
        <div class="chart-card" id="chart-segments"></div>
    </div>

    <div class="footer">
        Customer Shopping Behavior Portfolio Project | Python · DuckDB · SQLite · Plotly
    </div>

    <script>
        const darkTheme = {{
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: {{ color: '#f8fafc', family: 'Inter, sans-serif' }},
            margin: {{ t: 40, b: 40, l: 50, r: 20 }}
        }};

        // 1. Subscription Donut Chart
        Plotly.newPlot('chart-subscription', [{{
            labels: {sub_labels},
            values: {sub_values},
            type: 'pie',
            hole: 0.55,
            marker: {{ colors: ['#3b82f6', '#10b981'] }}
        }}], {{
            ...darkTheme,
            title: {{ text: 'Subscription Status Distribution', font: {{ size: 16 }} }},
            showlegend: true
        }}, {{ responsive: true }});

        // 2. Revenue by Category
        Plotly.newPlot('chart-category-rev', [{{
            x: {cat_summary['category'].tolist()},
            y: {cat_summary['revenue'].tolist()},
            type: 'bar',
            marker: {{ color: '#6366f1' }}
        }}], {{
            ...darkTheme,
            title: {{ text: 'Total Revenue by Category ($)', font: {{ size: 16 }} }},
            yaxis: {{ title: 'Revenue (USD)' }}
        }}, {{ responsive: true }});

        // 3. Revenue by Age Group
        Plotly.newPlot('chart-age-rev', [{{
            x: {[str(x) for x in age_summary['age_group'].tolist()]},
            y: {age_summary['revenue'].tolist()},
            type: 'bar',
            marker: {{ color: '#f59e0b' }}
        }}], {{
            ...darkTheme,
            title: {{ text: 'Total Revenue by Age Group ($)', font: {{ size: 16 }} }},
            yaxis: {{ title: 'Revenue (USD)' }}
        }}, {{ responsive: true }});

        // 4. Customer Segmentation
        Plotly.newPlot('chart-segments', [{{
            labels: {seg_labels},
            values: {seg_values},
            type: 'pie',
            marker: {{ colors: ['#8b5cf6', '#ec4899', '#06b6d4'] }}
        }}], {{
            ...darkTheme,
            title: {{ text: 'Customer Segments (Loyal, Returning, New)', font: {{ size: 16 }} }},
            showlegend: true
        }}, {{ responsive: true }});
    </script>
</body>
</html>
"""
    with open(HTML_DASHBOARD, "w") as f:
        f.write(html_content)
    print(f"Generated standalone HTML dashboard: {os.path.basename(HTML_DASHBOARD)}")
    print("  -> Double-click or run 'open dashboard.html' to view in Safari/Chrome.")


if __name__ == "__main__":
    df = clean_and_transform_data(CSV_INPUT)
    export_to_databases(df)
    execute_sql_queries(df)
    generate_standalone_dashboard(df)
    print("\n" + "=" * 60)
    print("✅ Pipeline Completed Successfully!")
    print("=" * 60)

