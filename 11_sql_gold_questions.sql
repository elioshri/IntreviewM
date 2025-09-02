/**********************************************************************
📌 11 – SQL Gold Questions (Advanced Data Analyst)

שאלות מתקדמות, עם פתרונות והסברים, במיוחד ל-SQL Server
**********************************************************************/

----------------------------------------------------------------------
-- Q1: חלון – מצא את ההזמנה השנייה בגודלה לכל לקוח
----------------------------------------------------------------------

SELECT customer_id, order_id, amount
FROM (
    SELECT customer_id, order_id, amount,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rnk
    FROM dbo.Orders
) t
WHERE rnk = 2;

-- הסבר: ROW_NUMBER מחלק לכל שורה דירוג לפי סדר; מסנן את ה-2.

----------------------------------------------------------------------
-- Q2: ממוצע נע ל-3 הזמנות אחרונות לכל לקוח
----------------------------------------------------------------------

SELECT customer_id, order_id, order_date, amount,
       AVG(amount*1.0) OVER (
            PARTITION BY customer_id
            ORDER BY order_date
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
       ) AS avg_last3
FROM dbo.Orders;

-- הסבר: חלון עם ROWS BETWEEN מאפשר להסתכל אחורה על מספר רשומות.

----------------------------------------------------------------------
-- Q3: CTE רקורסיבי – טבלת תאריכים בין שתי נקודות
----------------------------------------------------------------------

WITH Dates AS (
    SELECT CAST('2025-01-01' AS DATE) AS d
    UNION ALL
    SELECT DATEADD(DAY,1,d)
    FROM Dates
    WHERE d < '2025-01-10'
)
SELECT * FROM Dates;

-- הסבר: יוצרת סדרת תאריכים (10 ימים) בלי טבלת עזר.

----------------------------------------------------------------------
-- Q4: Pivot – סכום מכירות לפי חודש ולקוח
----------------------------------------------------------------------

SELECT *
FROM (
    SELECT customer_id, FORMAT(order_date,'yyyy-MM') AS ym, amount
    FROM dbo.Orders
) src
PIVOT (
    SUM(amount) FOR ym IN ([2025-01],[2025-02],[2025-03])
) p;

-- הסבר: הופך שורות לעמודות; בריאיון אפשר גם להשתמש ב-pivot_table ב-pandas.

----------------------------------------------------------------------
-- Q5: Anti-Join – מציאת לקוחות ללא הזמנות
----------------------------------------------------------------------

SELECT c.customer_id, c.name
FROM dbo.Customers c
LEFT JOIN dbo.Orders o
  ON c.customer_id = o.customer_id
WHERE o.customer_id IS NULL;

-- הסבר: LEFT JOIN + WHERE IS NULL = רשומות ללא התאמה.

----------------------------------------------------------------------
-- Q6: Rank אחוזי (Percent Rank) ללקוחות לפי מכירות
----------------------------------------------------------------------

SELECT customer_id, SUM(amount) AS total,
       PERCENT_RANK() OVER (ORDER BY SUM(amount)) AS pct_rank
FROM dbo.Orders
GROUP BY customer_id;

----------------------------------------------------------------------
-- Q7: Detect duplicates – מצא לקוחות כפולים באותה עיר
----------------------------------------------------------------------

SELECT name, city, COUNT(*) AS cnt
FROM dbo.Customers
GROUP BY name, city
HAVING COUNT(*) > 1;

----------------------------------------------------------------------
-- Q8: CTE עם חלון – Top 3 מכירות ליום
----------------------------------------------------------------------

WITH ranked AS (
  SELECT order_date, order_id, amount,
         ROW_NUMBER() OVER (PARTITION BY order_date ORDER BY amount DESC) AS rnk
  FROM dbo.Orders
)
SELECT *
FROM ranked
WHERE rnk <= 3;

----------------------------------------------------------------------
-- Q9: Running Total + Partition
----------------------------------------------------------------------

SELECT customer_id, order_date, amount,
       SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM dbo.Orders;

----------------------------------------------------------------------
-- Q10: דוחות מורכבים – חלוקת הכנסות ל-Quartiles
----------------------------------------------------------------------

WITH sums AS (
  SELECT customer_id, SUM(amount) AS total
  FROM dbo.Orders
  GROUP BY customer_id
)
SELECT customer_id, total,
       NTILE(4) OVER (ORDER BY total DESC) AS quartile
FROM sums;

----------------------------------------------------------------------
-- 💡 טיפים:
-- • השתמש תמיד ב-CTE כדי לפשט שאילתות מורכבות.
-- • תזכור את ההבדל בין ROW_NUMBER, RANK, DENSE_RANK.
-- • ל-Running Totals עדיף חלון SUM OVER מאשר סאב-קווירי.
-- • Anti-Join (LEFT JOIN … IS NULL) – שאלה מאוד פופולרית.
-- • NTILE עוזר לחלוקת קהלים (quartiles/deciles).
----------------------------------------------------------------------
