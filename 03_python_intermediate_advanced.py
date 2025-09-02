######################################################################
# 📌 03 – Python Intermediate → Advanced (דאטא אנליסט)
#
# מה יש פה:
#  1) Comprehensions, itertools, collections
#  2) Generators, iterators, yield from
#  3) Regex, pathlib, קבצים, JSON / CSV / Parquet (קריאה/כתיבה)
#  4) חריגות, Context Managers, Decorators קצרים
#  5) OOP קצר + dataclasses + typing
#  6) יעילות: טיפים לביצועים + מדידה
#  7) pandas טריקים (merge_asof, groupby מתקדמות, קטגוריות, אופטימיזציה)
#  8) חיבור למסד נתונים (SQLAlchemy) – קריאה/כתיבה
#  9) בדיקות (pytest) – תבנית קצרה
######################################################################

# ==============================================================
# 1) Comprehensions, itertools, collections
# ==============================================================

# List/Dict/Set Comprehensions – קריא ומהיר מקוד פורמלי
nums = [1, 2, 3, 4, 5]
squares = [n*n for n in nums if n % 2 == 1]     # [1, 9, 25]
pairs   = {(i, j) for i in [1,2] for j in [3,4]}# {(1,3),(1,4),(2,3),(2,4)}
dmap    = {n: n**2 for n in nums}               # {1:1, 2:4, ...}

# itertools – כלים חזקים לעבודה איטרטיבית
import itertools as it
letters = ['a','b','c']
prod = list(it.product(nums, letters))  # מכפלה קרטזית
accu = list(it.accumulate([1,2,3,4]))   # [1,3,6,10] סכום מצטבר (יש גם max, mul)

# collections – כלים שימושיים מאוד
from collections import Counter, defaultdict, deque, namedtuple

cnt = Counter("banana")                 # ספירת תווים/פריטים
print(cnt.most_common(1))               # [('a', 3)]
dd = defaultdict(int)
for x in [1,1,2,3]: dd[x] += 1          # מילון עם ערך ברירת מחדל 0
q = deque([1,2,3]); q.appendleft(0); q.pop()

Point = namedtuple("Point", "x y")
p = Point(10, 20)                       # כמו טופל עם שמות שדות


# ==============================================================
# 2) Generators, iterators, yield from
# ==============================================================

def countdown(n: int):
    """גנרטור – מחזיר ערכים "תוך כדי תנועה" (חסכוני בזיכרון)."""
    while n > 0:
        yield n
        n -= 1

print(list(countdown(3)))               # [3,2,1]

def chain_iterables(*iters):
    """דוגמה ל-yield from – שט扁 איטרטורים."""
    for itx in iters:
        yield from itx

print(list(chain_iterables([1,2], (3,4), range(5,7))))  # [1,2,3,4,5,6]


# ==============================================================
# 3) Regex, pathlib, קבצים, JSON/CSV/Parquet
# ==============================================================

import re, json, csv, os
from pathlib import Path

# Regex – חילוץ דומיין מאימייל
email = "user.name+tag@company.co.il"
m = re.search(r"@([\w.-]+)$", email)
domain = m.group(1) if m else None

# pathlib – עבודה נקייה עם נתיבים
base = Path.cwd() / "data_demo"
base.mkdir(exist_ok=True)

# כתיבה/קריאה JSON (ensure_ascii=False לתמיכה בעברית)
doc = {"id": 1, "name": "Eli", "tags": ["vip","israel"]}
with open(base/"example.json", "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)

with open(base/"example.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)

# CSV – כתיבה/קריאה מהירה
rows = [{"order_id":101,"amount":120.5},{"order_id":102,"amount":89.9}]
with open(base/"orders.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["order_id","amount"])
    w.writeheader(); w.writerows(rows)

# Parquet (צריך pyarrow או fastparquet)
# pip install pyarrow
import pandas as pd
df = pd.DataFrame(rows)
df.to_parquet(base/"orders.parquet", index=False)
df_back = pd.read_parquet(base/"orders.parquet")


# ==============================================================
# 4) חריגות, Context Managers, Decorators
# ==============================================================

# חריגות
def safe_div(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return float("inf")
    except Exception as e:
        # לוג/טיפול כללי
        return None

# Context Manager – שימוש ב-with מעבר לקבצים
from contextlib import contextmanager
@contextmanager
def change_dir(path: Path):
    """מחליף ספרייה זמנית ואז חוזר."""
    old = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)

with change_dir(base):
    # בתוך ה-with cwd = base
    pass

# Decorator – מדידת זמן ריצה
import time
def timed(func):
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        out = func(*args, **kwargs)
        t1 = time.perf_counter()
        print(f"[timed] {func.__name__} took {(t1-t0)*1000:.2f} ms")
        return out
    return wrapper

@timed
def slow_sum(n: int) -> int:
    s = 0
    for i in range(n): s += i
    return s

_ = slow_sum(200000)


# ==============================================================
# 5) OOP קצר + dataclasses + typing
# ==============================================================

from dataclasses import dataclass
from typing import List, Dict, Optional, Iterable, Tuple

@dataclass
class Order:
    order_id: int
    amount: float
    customer_id: int
    def with_vat(self, rate: float = 0.17) -> float:
        return round(self.amount * (1 + rate), 2)

orders_list: List[Order] = [
    Order(101, 120.5, 1),
    Order(102, 89.9,  1),
    Order(103, 300.0, 2),
]

def totals_by_customer(orders: Iterable[Order]) -> Dict[int, float]:
    out: Dict[int, float] = defaultdict(float)
    for o in orders:
        out[o.customer_id] += o.amount
    return out

print("totals_by_customer:", totals_by_customer(orders_list))


# ==============================================================
# 6) יעילות: טיפים לביצועים + מדידה
# ==============================================================

# טיפים:
# • הימנעו מלולאות פייתון איטיות על DataFrame – העדיפו וקטוריזציה/GroupBy.
# • list/dict/set מהירים יותר מלולאות חיפוש/append כבדות.
# • itertools/collections נותנים כלים יעילים מזיכרון/זמן.
# • מדדו עם time.perf_counter() או מודול timeit.

import timeit
print("list comprehension time:",
      timeit.timeit("[x*x for x in range(1000)]", number=1000))


# ==============================================================
# 7) pandas טריקים לשימוש יום-יומי של אנליסט
# ==============================================================

# נתוני דוגמה
orders = pd.DataFrame({
    "order_id":[1,2,3,4,5,6],
    "customer_id":[1,1,2,2,3,1],
    "order_ts": pd.to_datetime([
        "2025-07-01 10:00","2025-07-01 10:05","2025-07-01 11:00",
        "2025-07-02 09:00","2025-07-02 18:30","2025-07-03 08:15"
    ]),
    "amount":[120.0,80.0,50.0,150.0,300.0,90.0]
})

campaign = pd.DataFrame({
    "start_ts": pd.to_datetime(["2025-07-01 00:00","2025-07-02 00:00"]),
    "discount":[0.10, 0.20]
}).rename(columns={"start_ts":"ts"})

# 7.1 merge_asof – צירוף לפי ה"טיימסטמפ" האחרון לפני האירוע (אין דליפת עתיד)
orders_sorted = orders.sort_values("order_ts")
camp_sorted = campaign.sort_values("ts")
orders_asof = pd.merge_asof(
    orders_sorted, camp_sorted, left_on="order_ts", right_on="ts",
    direction="backward"
).drop(columns=["ts"])
print("\n=== merge_asof (join על קמפיין פעיל בזמן) ===\n", orders_asof)

# 7.2 groupby.transform – הוספת עמודת יחס/אחוז מתוך קבוצה
cust_sum = orders.groupby("customer_id")["amount"].transform("sum")
orders["pct_of_customer"] = orders["amount"] / cust_sum
print("\n=== pct_of_customer ===\n", orders[["order_id","customer_id","amount","pct_of_customer"]])

# 7.3 קטגוריות – חיסכון בזיכרון והאצה
orders["segment"] = pd.Categorical(
    ["A","A","B","B","C","A"], categories=["A","B","C"], ordered=True
)

# 7.4 אופטימיזציית זיכרון – downcast
big = pd.DataFrame({
    "i": pd.Series(range(0,10000), dtype="int64"),
    "f": pd.Series([1.0]*10000, dtype="float64")
})
big_opt = big.assign(
    i = pd.to_numeric(big["i"], downcast="integer"),
    f = pd.to_numeric(big["f"], downcast="float")
)
print("dtypes before:\n", big.dtypes, "\nafter:\n", big_opt.dtypes)

# 7.5 חלונות מתקדמים – rolling לפי מפתח (מיון חובה!)
orders = orders.sort_values(["customer_id","order_ts"])
orders["rolling2"] = (orders
                      .groupby("customer_id")["amount"]
                      .rolling(2, min_periods=1)
                      .mean()
                      .reset_index(level=0, drop=True))
print("\n=== rolling2 per customer ===\n", orders[["order_id","customer_id","amount","rolling2"]])

# 7.6 pivot_table → ואח"כ מילוי NaN + הוספת טור total
pv = (orders
      .assign(day=orders["order_ts"].dt.date)
      .pivot_table(index="day", columns="customer_id", values="amount", aggfunc="sum"))
pv = pv.fillna(0.0)
pv["total"] = pv.sum(axis=1)
print("\n=== pivot_table with total ===\n", pv)

# 7.7 בדיקות QA מהירות
assert orders["order_id"].is_unique, "order_id לא ייחודי"
assert orders["amount"].ge(0).all(), "amount שלילי לא תקין"


# ==============================================================
# 8) חיבור למסד נתונים (SQL Server) עם SQLAlchemy – קריאה/כתיבה
# ==============================================================

# pip install sqlalchemy pyodbc
# שים לב להתאים: USERNAME, PASSWORD, SERVER\INSTANCE, DATABASE, Driver
import sqlalchemy as sa

conn_str = (
    "mssql+pyodbc://USERNAME:PASSWORD@SERVER\\INSTANCE/DATABASE"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)
# הערה: בראיון מספיק להראות את התבנית; אל תחשוף סיסמאות אמיתיות.

# engine = sa.create_engine(conn_str, fast_executemany=True)
# df_db = pd.read_sql("SELECT TOP 100 * FROM dbo.Orders", engine)
# df_db.to_sql("OrdersCopy", engine, if_exists="replace", index=False)


# ==============================================================
# 9) בדיקות (pytest) – תבנית קצרה
# ==============================================================

# שמור את הקטע הבא כ-test_example.py והרץ:  pytest -q
"""
import pandas as pd

def normalize_pct(s: pd.Series) -> pd.Series:
    total = s.sum()
    return s / total if total else s

def test_normalize_pct():
    s = pd.Series([1,1,2])
    out = normalize_pct(s)
    assert round(out.sum(), 6) == 1.0
    assert out.iloc[2] > out.iloc[0]
"""

######################################################################
# 💡 TL;DR – טיפים חשובים:
# • itertools/collections חוסכים זמן וזיכרון (accumulate, product, Counter).
# • עדיפות לגנרטורים (yield) כשזיכרון יקר/זרם נתונים ארוך.
# • pandas: לפני rolling/cumsum בצעו sort_values לפי מקשי קבוצה.
# • merge_asof מצוין לצירופי timeline (קמפיינים, קונפיגים, שערי מט"ח).
# • הקפידו על טיפוסי נתונים: Categorical, downcast → חיסכון גדול בזיכרון.
# • כתבו בדיקות קטנות לטרנספורמציות קריטיות (QA של דאטה).
# • מדדו! time/perf_counter/timeit – אל תנחשו איפה צוואר הבקבוק.
######################################################################
