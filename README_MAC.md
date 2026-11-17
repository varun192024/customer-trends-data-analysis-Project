# 🛍️ Customer Shopping Behavior Analysis — macOS End-to-End Edition

This repository contains the complete, industry-standard, end-to-end data analytics workflow for the **Customer Shopping Behavior Portfolio Project**, fully configured and optimized for **macOS**.

---

## 🍏 Power BI on macOS: The Challenge & The Solution

### Why Power BI Desktop Doesn't Run on macOS
Microsoft **Power BI Desktop is exclusively built for Windows** using the Windows Presentation Foundation (WPF) and DirectX frameworks. Microsoft does not offer a native macOS application. Mac users traditionally must rely on heavy Windows virtual machines (Parallels / VMware) or the limited Power BI Web Service.

### The Mac-Native Solution Implemented in this Repo
To deliver an **authentic, interactive, and production-grade end-to-end experience** on macOS, we have implemented:

1. **Interactive Streamlit Web Dashboard (`app.py`)**:
   - Replicates and enhances the full Power BI report layout.
   - **Interactive Slicers:** Filter dynamically by *Subscription Status, Gender, Category, Shipping Type, Age Group, and Season*.
   - **Power BI KPI Cards:** Total Customers (3,900), Total Revenue ($233.08K), Average Purchase Amount ($59.76), Average Rating (3.75★).
   - **Visuals:** Subscription Donut Chart, Revenue by Category, Orders by Category, Revenue by Age Group, Customer Count by Age Group, Customer Loyalty Segments, Shipping Impact.
   - **Live SQL Query Explorer:** Direct interactive execution of all 10 business questions and an interactive SQL sandbox.
   - **Data Explorer:** Searchable dataset with one-click CSV export.

2. **Standalone Interactive HTML Dashboard (`dashboard.html`)**:
   - Built with Plotly.js for instant viewing in Safari, Chrome, or any web browser without needing any server running (`open dashboard.html`).

3. **DuckDB & SQLite Database Engines (`customer_behavior.duckdb` & `customer_behavior.db`)**:
   - Zero-server-installation SQL databases.
   - Directly executes PostgreSQL dialect queries (`::numeric`, window functions `ROW_NUMBER() OVER (...)`) without configuring pgAdmin or external services.

4. **Automated End-to-End Pipeline (`run_pipeline.py`)**:
   - One-command script that cleans the raw data, imputes missing values, engineers features, exports to SQLite/DuckDB, runs all 10 SQL queries, and generates reports.

---

## 🚀 Quick Start (One-Command Launch)

### 1. Launch the Interactive Dashboard
```bash
cd customer-trends-data-analysis-SQL-Python-PowerBI
./run_dashboard.sh
```
> The dashboard will start and open automatically in your browser at `http://localhost:8501`.

### 2. Run the Data Pipeline & SQL Analysis
```bash
./run_pipeline.sh
```
> Cleans `customer_shopping_behavior.csv`, populates SQLite/DuckDB databases, runs all 10 business queries, and updates `sql_query_results.md` and `dashboard.html`.

### 3. Open the Standalone Offline Dashboard
```bash
./open_dashboard.sh
# or simply:
open dashboard.html
```

---

## 📁 Repository Structure

```text
customer-trends-data-analysis-SQL-Python-PowerBI/
├── app.py                                   # Streamlit Interactive Dashboard (Power BI Alternative)
├── dashboard.html                           # Standalone offline Plotly HTML dashboard
├── run_pipeline.py                          # Automated data cleaning, feature engineering & SQL runner
├── run_dashboard.sh                         # Shell launcher for Streamlit dashboard
├── run_pipeline.sh                          # Shell runner for pipeline
├── open_dashboard.sh                        # Shell launcher for standalone dashboard
├── customer_shopping_behavior.csv           # Raw dataset (3,900 rows, 18 columns)
├── customer_shopping_behavior_cleaned.csv   # Cleaned dataset with engineered features
├── customer_behavior.db                     # SQLite database (table: customer)
├── customer_behavior.duckdb                 # DuckDB database (table: customer)
├── customer_behavior_sql_queries.sql        # The 10 business SQL queries
├── sql_query_results.md                     # Markdown summary of all 10 SQL query outputs & insights
├── Customer_Shopping_Behavior_Analysis.ipynb# Jupyter notebook (pre-configured with local SQL)
├── customer_behavior_dashboard.pbix         # Original Power BI file (Windows only)
├── requirements.txt                         # Python dependencies
├── README_MAC.md                            # macOS comprehensive guide (this file)
└── venv/                                    # Dedicated Python virtual environment
```

---

## 📊 Summary of the 10 Business Questions & Key Findings

| # | Business Question | Key Finding |
|---|---|---|
| **Q1** | Revenue by Gender | Male: **$157,890 (67.7%)**, Female: **$75,191 (32.3%)** |
| **Q2** | High-Spending Discount Users | **839 shoppers** used discounts and spent ≥ average, averaging **$79.79** per order |
| **Q3** | Top 5 Products by Rating | **Gloves (3.86★)**, **Sandals (3.84★)**, **Boots (3.82★)**, **Hat (3.80★)**, **T-shirt (3.78★)** |
| **Q4** | Standard vs. Express Shipping | Express customers spend **$60.48** avg vs **$58.46** for Standard (~3.5% premium) |
| **Q5** | Subscribed vs. Non-Subscribed | Subscribers: **1,053 (27%)**, $62.6K revenue; avg spend is equal (~$59.50 vs ~$59.87) |
| **Q6** | Top 5 Discounted Products | **Hat (50.0%)**, **Sneakers (49.7%)**, **Coat (49.1%)**, **Sweater (48.2%)**, **Pants (47.4%)** |
| **Q7** | Customer Segmentation | **Loyal: 79.9% (3,116)**, **Returning: 18.0% (701)**, **New: 2.1% (83)** |
| **Q8** | Top 3 Products per Category | Clothing (Blouse, Pants, Shirt), Accessories (Jewelry, Sunglasses, Belt) |
| **Q9** | Repeat Buyers Subscription Rate | **72.4% (2,518)** of repeat buyers (>5 purchases) are **NOT** subscribed — prime upsell target |
| **Q10**| Revenue by Age Group | Young Adult: **$62.1K (26.7%)**, Middle-aged: **$59.2K (25.4%)**, Adult: **$56.0K**, Senior: **$55.8K** |

---

## 🛠️ Working with Jupyter Notebook on macOS

To run the notebook interactively:
```bash
./venv/bin/jupyter notebook Customer_Shopping_Behavior_Analysis.ipynb
```
Select the pre-registered kernel: **`Python (Customer Behavior Env)`**.

Cells 1–18 will run end-to-end without requiring any external database installations.

