/**********************************************************************
* 📌 12 – SQL INTERVIEW MEGA (T-SQL)
* מאגר שאלות-ראיון מלא + פתרונות + הסברים בעברית (SQL Server)
*
* סכמות דמו (הנח לצורך השאלות; שנה שמות לפי הצורך):
*   dbo.Customers(CustomerID PK, CustomerName, City, SignupDate)
*   dbo.Orders(OrderID PK, CustomerID FK, OrderDate, Amount, Status)
*   dbo.OrderItems(OrderItemID PK, OrderID FK, ProductID FK, Qty, UnitPrice)
*   dbo.Products(ProductID PK, ProductName, Category)
*   dbo.Payments(PaymentID PK, OrderID FK, PaidAt, Method, Amount)
*   dbo.WebEvents(EventID PK, CustomerID, EventType, OccurredAt, MetaJson NVARCHAR(MAX))
*
* טיפים כלליים למבחן:
*  • כתוב SARGable (ללא פונקציות על העמודה בצד WHERE).
*  • הראה מודעות ל-NULL, לדליפת זמן, ולכפילויות אחרי JOIN.
*  • העדף CTE לשאילתות מורכבות; בדוק תמיד KEY ייחודי בצד ימין לפני MERGE/JOIN.
**********************************************************************/

----------------------------------------------------------------------
-- Q1) Top-N לכל לקוח: ההזמנה היקרה ביותר לכל לקוח
----------------------------------------------------------------------

WITH ranked AS (
  SELECT o.CustomerID, o.OrderID, o.Amount,
         ROW_NUMBER() OVER (PARTITION BY o.CustomerID ORDER BY o.Amount DESC) AS rn
  FROM dbo.Orders o
)
SELECT CustomerID, OrderID, Amount
FROM ranked
WHERE rn = 1;
-- הסבר: ROW_NUMBER נותן דירוג; rn=1 הוא היקר ביותר פר לקוח.

----------------------------------------------------------------------
-- Q2) הזמנה אחרונה לכל לקוח (לפי תאריך) + סכום ההזמנה
----------------------------------------------------------------------

WITH r AS (
  SELECT o.CustomerID, o.OrderID, o.OrderDate, o.Amount,
         ROW_NUMBER() OVER (PARTITION BY o.CustomerID ORDER BY o.OrderDate DESC) AS rn
  FROM dbo.Orders o
)
SELECT CustomerID, OrderID, OrderDate, Amount
FROM r
WHERE rn = 1;
-- הסבר: דפוס "האחרון לכל קבוצה".

----------------------------------------------------------------------
-- Q3) ממוצע נע ל-3 הזמנות קודמות לכל לקוח (ללא דליפת עתיד)
----------------------------------------------------------------------

SELECT CustomerID, OrderID, OrderDate, Amount,
       AVG(Amount*1.0) OVER (
          PARTITION BY CustomerID
          ORDER BY OrderDate
          ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
       ) AS avg_prev3
FROM dbo.Orders;
-- הסבר: חלון מסתיים בשורה שלפני הנוכחית → אין שימוש בעתיד.

----------------------------------------------------------------------
-- Q4) שיעור הלקחות ב-Percentile (PERCENT_RANK) לפי סך קניות
----------------------------------------------------------------------

WITH sums AS (
  SELECT CustomerID, SUM(Amount) AS total_amt
  FROM dbo.Orders
  GROUP BY CustomerID
)
SELECT CustomerID, total_amt,
       PERCENT_RANK() OVER (ORDER BY total_amt) AS pct_rank
FROM sums;
-- הסבר: מדרג לקוחות באחוזונים לפי היקף כספי.

----------------------------------------------------------------------
-- Q5) לקוחות שלא ביצעו אף הזמנה (Anti-Join)
----------------------------------------------------------------------

SELECT c.CustomerID, c.CustomerName
FROM dbo.Customers c
LEFT JOIN dbo.Orders o ON o.CustomerID = c.CustomerID
WHERE o.OrderID IS NULL;
-- הסבר: LEFT JOIN + WHERE ... IS NULL = אנטי־ג'וין.

----------------------------------------------------------------------
-- Q6) הזמנות ללא תשלום מלא (QA פיננסי) – לפי Orders מול Payments
----------------------------------------------------------------------

WITH pay AS (
  SELECT o.OrderID, o.Amount AS order_amt, ISNULL(SUM(p.Amount),0) AS paid
  FROM dbo.Orders o
  LEFT JOIN dbo.Payments p ON p.OrderID = o.OrderID
  GROUP BY o.OrderID, o.Amount
)
SELECT OrderID, order_amt, paid, (order_amt - paid) AS balance
FROM pay
WHERE paid < order_amt;
-- הסבר: צירוף + אגרגציית תשלומים; חיפוש יתרות.

----------------------------------------------------------------------
-- Q7) הוצאות חודשיות (סכום Amount לפי yyyy-MM)
----------------------------------------------------------------------

SELECT FORMAT(OrderDate, 'yyyy-MM') AS ym,
       SUM(Amount) AS total_sales
FROM dbo.Orders
GROUP BY FORMAT(OrderDate, 'yyyy-MM')
ORDER BY ym;
-- הסבר: דוח חודשי קלאסי. לדיוק ביצועים, שקול EOMONTH/DATEFROMPARTS.

----------------------------------------------------------------------
-- Q8) Products: שלושת המוצרים הנמכרים ביותר בכמות (Top-3)
----------------------------------------------------------------------

SELECT TOP (3) p.ProductID, p.ProductName,
       SUM(oi.Qty) AS total_qty
FROM dbo.OrderItems oi
JOIN dbo.Products p ON p.ProductID = oi.ProductID
GROUP BY p.ProductID, p.ProductName
ORDER BY total_qty DESC;
-- הסבר: TOP עם ORDER BY על סיכום כמות.

----------------------------------------------------------------------
-- Q9) מחיר ממוצע להזמנה (AOV) פר לקוח
----------------------------------------------------------------------

SELECT o.CustomerID,
       AVG(o.Amount*1.0) AS avg_order_value
FROM dbo.Orders o
GROUP BY o.CustomerID
ORDER BY avg_order_value DESC;

----------------------------------------------------------------------
-- Q10) QA: מצא כפילויות ב-Orders לפי (CustomerID, OrderDate, Amount)
----------------------------------------------------------------------

SELECT CustomerID, OrderDate, Amount, COUNT(*) AS cnt
FROM dbo.Orders
GROUP BY CustomerID, OrderDate, Amount
HAVING COUNT(*) > 1;
-- הסבר: זיהוי כפילויות חזק לפני מודלים/דוחות.

----------------------------------------------------------------------
-- Q11) הסרת כפילויות (שמירת "ראשונה") עם ROW_NUMBER + DELETE
----------------------------------------------------------------------

WITH d AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY CustomerID, OrderDate, Amount ORDER BY OrderID) AS rn
  FROM dbo.Orders
)
DELETE FROM d WHERE rn > 1;
-- הסבר: מחיקה מבוססת חלון על CTE.

----------------------------------------------------------------------
-- Q12) QA זמן – מצא אירועים בעתיד ביחס ל-SignupDate (דליפת זמן)
----------------------------------------------------------------------

SELECT c.CustomerID, c.SignupDate, we.EventID, we.EventType, we.OccurredAt
FROM dbo.Customers c
JOIN dbo.WebEvents we ON we.CustomerID = c.CustomerID
WHERE we.OccurredAt < c.SignupDate; -- או > לפי הקונטקסט
-- הסבר: דגלי איכות נתונים.

----------------------------------------------------------------------
-- Q13) JSON: חילוץ שדות מה־MetaJson + אינדוקס מהיר (Persisted)
----------------------------------------------------------------------

-- יצירת עמודה מחושבת (DBA/הרשאות): 
-- ALTER TABLE dbo.WebEvents
-- ADD Country AS JSON_VALUE(MetaJson, '$.geo.country') PERSISTED;
-- CREATE INDEX IX_WebEvents_Country ON dbo.WebEvents(Country);

-- שליפה:
SELECT EventID, CustomerID,
       JSON_VALUE(MetaJson, '$.geo.country') AS Country,
       JSON_VALUE(MetaJson, '$.device.os')   AS OS
FROM dbo.WebEvents
WHERE JSON_VALUE(MetaJson, '$.geo.country') = 'IL';
-- הסבר: JSON_VALUE לתת־שדה; Persisted + אינדקס → SARGable.

----------------------------------------------------------------------
-- Q14) Pivot: סכום הכנסות לפי חודש × קטגוריית מוצר
----------------------------------------------------------------------

SELECT *
FROM (
  SELECT FORMAT(o.OrderDate,'yyyy-MM') AS ym,
         p.Category,
         oi.Qty * oi.UnitPrice AS line_amount
  FROM dbo.OrderItems oi
  JOIN dbo.Orders o   ON o.OrderID   = oi.OrderID
  JOIN dbo.Products p ON p.ProductID = oi.ProductID
) s
PIVOT (
  SUM(line_amount) FOR Category IN ([Shoes],[Shirts],[Hats],[Other])
) pv
ORDER BY ym;
-- הסבר: דוגמת pivot סטטית; לדינמי → STRING_AGG + sp_executesql.

----------------------------------------------------------------------
-- Q15) מציאת פערים ורצפים (Gaps & Islands) בימים עם הזמנות
----------------------------------------------------------------------

WITH d AS (
  SELECT CAST(OrderDate AS DATE) AS d,
         ROW_NUMBER() OVER (ORDER BY CAST(OrderDate AS DATE)) AS rn
  FROM dbo.Orders
  GROUP BY CAST(OrderDate AS DATE)
),
g AS (
  SELECT d, DATEADD(DAY, -rn, d) AS grp
  FROM d
)
SELECT MIN(d) AS island_start, MAX(d) AS island_end, COUNT(*) AS days
FROM g
GROUP BY grp
ORDER BY island_start;
-- הסבר: טריק (date - row_number) לאיגוד ימים רציפים.

----------------------------------------------------------------------
-- Q16) Top-K פר קבוצה עם CROSS APPLY (תבנית יעילה)
----------------------------------------------------------------------

SELECT c.CustomerID, x.OrderID, x.Amount
FROM dbo.Customers c
CROSS APPLY (
  SELECT TOP 3 o.OrderID, o.Amount
  FROM dbo.Orders o
  WHERE o.CustomerID = c.CustomerID
  ORDER BY o.Amount DESC
) AS x;
-- הסבר: CROSS APPLY מחלץ טופ-N לכל שורה.

----------------------------------------------------------------------
-- Q17) Inner/Left/Full Join – תרגול קצר עם סטטוס לקוח
----------------------------------------------------------------------

SELECT c.CustomerID, c.CustomerName, o.OrderID
FROM dbo.Customers c
LEFT JOIN dbo.Orders o ON o.CustomerID = c.CustomerID;
-- הסבר: LEFT כדי לכלול גם לקוחות ללא הזמנות.

----------------------------------------------------------------------
-- Q18) מדד אחוז הכנסה לקטגוריה מתוך כלל הכנסות
----------------------------------------------------------------------

WITH cat AS (
  SELECT p.Category, SUM(oi.Qty * oi.UnitPrice) AS sales
  FROM dbo.OrderItems oi
  JOIN dbo.Products p ON p.ProductID = oi.ProductID
  GROUP BY p.Category
), tot AS (
  SELECT SUM(sales) AS total_sales FROM cat
)
SELECT c.Category, c.sales,
       CAST(100.0 * c.sales / NULLIF(t.total_sales,0) AS DECIMAL(6,2)) AS pct
FROM cat c CROSS JOIN tot t
ORDER BY pct DESC;
-- הסבר: חישוב אחוזים מול סך הכל.

----------------------------------------------------------------------
-- Q19) Rank מול DenseRank – להבין הבדל כשיש "תיקו"
----------------------------------------------------------------------

WITH sums AS (
  SELECT CustomerID, SUM(Amount) AS total
  FROM dbo.Orders
  GROUP BY CustomerID
)
SELECT CustomerID, total,
       RANK()       OVER (ORDER BY total DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY total DESC) AS drnk
FROM sums
ORDER BY total DESC;
-- הסבר: RANK מדלג בדרגות, DENSE_RANK לא.

----------------------------------------------------------------------
-- Q20) Rolling חודשי (Moving Average 3 חודשים) – ברמת חודש
----------------------------------------------------------------------

WITH m AS (
  SELECT EOMONTH(OrderDate) AS m_end,
         SUM(Amount) AS m_sales
  FROM dbo.Orders
  GROUP BY EOMONTH(OrderDate)
)
SELECT m_end, m_sales,
       AVG(m_sales*1.0) OVER (ORDER BY m_end ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma3
FROM m
ORDER BY m_end;

----------------------------------------------------------------------
-- Q21) Percentile דיסקרטי לפי חלון – NTILE(10) לעשירונים
----------------------------------------------------------------------

WITH sums AS (
  SELECT CustomerID, SUM(Amount) AS total
  FROM dbo.Orders
  GROUP BY CustomerID
)
SELECT CustomerID, total,
       NTILE(10) OVER (ORDER BY total DESC) AS decile
FROM sums;

----------------------------------------------------------------------
-- Q22) Anti-pattern → תיקון: WHERE YEAR(OrderDate)=2025 (שובר אינדקס)
----------------------------------------------------------------------

-- ❌ לא מומלץ:
-- SELECT * FROM dbo.Orders WHERE YEAR(OrderDate) = 2025;

-- ✅ SARGable:
SELECT * FROM dbo.Orders
WHERE OrderDate >= '2025-01-01'
  AND OrderDate <  '2026-01-01';
-- הסבר: מאפשר Index Seek.

----------------------------------------------------------------------
-- Q23) Filtered Index תבנית (דורש DBA) + שימוש נכון בשאילתה
----------------------------------------------------------------------

-- CREATE NONCLUSTERED INDEX IX_Orders_Active
--   ON dbo.Orders(CustomerID, OrderDate)
--   WHERE Status = 'Active';

SELECT OrderID, CustomerID, Amount
FROM dbo.Orders
WHERE Status = 'Active' AND OrderDate >= '2025-01-01';
-- הסבר: מסנכרן predicate עם ה-Filtered Index.

----------------------------------------------------------------------
-- Q24) זיהוי "לקוחות רדומים": לא הזמינו 90 יום אחרונים
----------------------------------------------------------------------

SELECT c.CustomerID, c.CustomerName
FROM dbo.Customers c
LEFT JOIN (
  SELECT CustomerID, MAX(OrderDate) AS last_order
  FROM dbo.Orders
  GROUP BY CustomerID
) x ON x.CustomerID = c.CustomerID
WHERE ISNULL(x.last_order, '1900-01-01') < DATEADD(DAY, -90, CAST(GETDATE() AS DATE));
-- הסבר: השוואה מול היום; אפשר לעטוף בפרמטר @asof
