# 📊 SQL Business Queries & Analysis Results

> Generated automatically by `run_pipeline.py` using DuckDB/SQLite engine.

## Q1: Total Revenue by Gender

```sql
SELECT gender, SUM(purchase_amount) AS revenue,
       ROUND(100.0 * SUM(purchase_amount) / (SELECT SUM(purchase_amount) FROM customer), 2) AS revenue_share_pct
FROM customer
GROUP BY gender
ORDER BY revenue DESC;
```

**Results:**

| gender   |   revenue |   revenue_share_pct |
|:---------|----------:|--------------------:|
| Male     |    157890 |               67.74 |
| Female   |     75191 |               32.26 |

💡 **Key Insight:** Male customers contribute ~$157.9K (67.7%) of total revenue, while Female customers contribute ~$75.2K (32.3%).

---

## Q2: High-Spending Discount Users

```sql
SELECT customer_id, purchase_amount, category, item_purchased
FROM customer 
WHERE discount_applied = 'Yes' 
  AND purchase_amount >= (SELECT AVG(purchase_amount) FROM customer)
LIMIT 10;
```

**Results:**

|   customer_id |   purchase_amount | category   | item_purchased   |
|--------------:|------------------:|:-----------|:-----------------|
|             2 |                64 | Clothing   | Sweater          |
|             3 |                73 | Clothing   | Jeans            |
|             4 |                90 | Footwear   | Sandals          |
|             7 |                85 | Clothing   | Shirt            |
|             9 |                97 | Outerwear  | Coat             |
|            12 |                68 | Clothing   | Shorts           |
|            13 |                72 | Outerwear  | Coat             |
|            16 |                81 | Clothing   | Skirt            |
|            20 |                90 | Clothing   | Pants            |
|            22 |                62 | Clothing   | Pants            |

💡 **Key Insight:** 839 customers used discounts yet spent at or above the average ($59.76), generating $66,940 total revenue at an average of $79.79 per order.

---

## Q3: Top 5 Products with Highest Average Review Rating

```sql
SELECT item_purchased, 
       ROUND(AVG(review_rating::numeric), 2) AS avg_rating,
       COUNT(*) AS total_purchases
FROM customer
GROUP BY item_purchased
ORDER BY avg_rating DESC
LIMIT 5;
```

**Results:**

| item_purchased   |   avg_rating |   total_purchases |
|:-----------------|-------------:|------------------:|
| Gloves           |         3.86 |               140 |
| Sandals          |         3.84 |               160 |
| Boots            |         3.82 |               144 |
| Hat              |         3.8  |               154 |
| Skirt            |         3.78 |               158 |

💡 **Key Insight:** Gloves (3.86), Sandals (3.84), Boots (3.82), Hat (3.80), and Skirt (3.78) hold the highest satisfaction scores.

---

## Q4: Average Purchase Amount: Standard vs. Express Shipping

```sql
SELECT shipping_type, 
       ROUND(AVG(purchase_amount), 2) AS avg_purchase_amount,
       COUNT(*) AS total_orders
FROM customer
WHERE shipping_type IN ('Standard', 'Express')
GROUP BY shipping_type;
```

**Results:**

| shipping_type   |   avg_purchase_amount |   total_orders |
|:----------------|----------------------:|---------------:|
| Standard        |                 58.46 |            654 |
| Express         |                 60.48 |            646 |

💡 **Key Insight:** Express shipping customers have an average spend of $60.48 compared to $58.46 for Standard shipping (~3.5% higher).

---

## Q5: Subscribed vs. Non-Subscribed Customers

```sql
SELECT subscription_status,
       COUNT(customer_id) AS total_customers,
       ROUND(AVG(purchase_amount), 2) AS avg_spend,
       ROUND(SUM(purchase_amount), 2) AS total_revenue,
       ROUND(100.0 * COUNT(customer_id) / (SELECT COUNT(*) FROM customer), 2) AS customer_pct
FROM customer
GROUP BY subscription_status
ORDER BY total_revenue DESC;
```

**Results:**

| subscription_status   |   total_customers |   avg_spend |   total_revenue |   customer_pct |
|:----------------------|------------------:|------------:|----------------:|---------------:|
| No                    |              2847 |       59.87 |          170436 |             73 |
| Yes                   |              1053 |       59.49 |           62645 |             27 |

💡 **Key Insight:** Subscribers make up 27% of customers (1,053) generating $62,645 in revenue. Average spend is almost identical ($59.49 vs $59.87).

---

## Q6: Top 5 Products with Highest Percentage of Discount Purchases

```sql
SELECT item_purchased,
       ROUND(100.0 * SUM(CASE WHEN discount_applied = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS discount_rate,
       COUNT(*) AS total_purchases
FROM customer
GROUP BY item_purchased
ORDER BY discount_rate DESC
LIMIT 5;
```

**Results:**

| item_purchased   |   discount_rate |   total_purchases |
|:-----------------|----------------:|------------------:|
| Hat              |           50    |               154 |
| Sneakers         |           49.66 |               145 |
| Coat             |           49.07 |               161 |
| Sweater          |           48.17 |               164 |
| Pants            |           47.37 |               171 |

💡 **Key Insight:** Hats (50.0%), Sneakers (49.66%), Coats (49.07%), Sweaters (48.17%), and Pants (47.37%) are most frequently bought with discounts.

---

## Q7: Customer Segmentation (New, Returning, Loyal)

```sql
WITH customer_type AS (
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
ORDER BY number_of_customers DESC;
```

**Results:**

| customer_segment   |   number_of_customers |   segment_pct |
|:-------------------|----------------------:|--------------:|
| Loyal              |                  3116 |         79.9  |
| Returning          |                   701 |         17.97 |
| New                |                    83 |          2.13 |

💡 **Key Insight:** 79.9% of customers (3,116) are categorized as Loyal (11+ previous purchases), 18.0% (701) are Returning, and 2.1% (83) are New.

---

## Q8: Top 3 Most Purchased Products within Each Category

```sql
WITH item_counts AS (
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
ORDER BY category, item_rank;
```

**Results:**

|   item_rank | category    | item_purchased   |   total_orders |
|------------:|:------------|:-----------------|---------------:|
|           1 | Accessories | Jewelry          |            171 |
|           2 | Accessories | Belt             |            161 |
|           3 | Accessories | Sunglasses       |            161 |
|           1 | Clothing    | Pants            |            171 |
|           2 | Clothing    | Blouse           |            171 |
|           3 | Clothing    | Shirt            |            169 |
|           1 | Footwear    | Sandals          |            160 |
|           2 | Footwear    | Shoes            |            150 |
|           3 | Footwear    | Sneakers         |            145 |
|           1 | Outerwear   | Jacket           |            163 |
|           2 | Outerwear   | Coat             |            161 |

💡 **Key Insight:** Top sellers include Blouse & Pants in Clothing (171 each), Jewelry in Accessories (171), Jacket in Outerwear (163), and Sandals in Footwear (160).

---

## Q9: Repeat Buyers (>5 purchases) Subscription Rate

```sql
SELECT subscription_status,
       COUNT(customer_id) AS repeat_buyers,
       ROUND(100.0 * COUNT(customer_id) / SUM(COUNT(customer_id)) OVER(), 2) AS pct_of_repeat_buyers
FROM customer
WHERE previous_purchases > 5
GROUP BY subscription_status;
```

**Results:**

| subscription_status   |   repeat_buyers |   pct_of_repeat_buyers |
|:----------------------|----------------:|-----------------------:|
| No                    |            2518 |                  72.44 |
| Yes                   |             958 |                  27.56 |

💡 **Key Insight:** Out of 3,476 repeat buyers (>5 purchases), 72.4% (2,518) are currently NON-subscribers. This represents a prime conversion opportunity.

---

## Q10: Revenue Contribution by Age Group

```sql
SELECT age_group,
       COUNT(customer_id) AS customer_count,
       ROUND(AVG(purchase_amount), 2) AS avg_spend,
       SUM(purchase_amount) AS total_revenue,
       ROUND(100.0 * SUM(purchase_amount) / (SELECT SUM(purchase_amount) FROM customer), 2) AS revenue_share_pct
FROM customer
GROUP BY age_group
ORDER BY total_revenue DESC;
```

**Results:**

| age_group   |   customer_count |   avg_spend |   total_revenue |   revenue_share_pct |
|:------------|-----------------:|------------:|----------------:|--------------------:|
| Young Adult |             1028 |       60.45 |           62143 |               26.66 |
| Middle-aged |              986 |       60.04 |           59197 |               25.4  |
| Adult       |              942 |       59.42 |           55978 |               24.02 |
| Senior      |              944 |       59.07 |           55763 |               23.92 |

💡 **Key Insight:** Young Adults lead with $62.1K (26.7%), followed by Middle-aged with $59.2K (25.4%), Adults with $56.0K (24.0%), and Seniors with $55.8K (23.9%).

---
