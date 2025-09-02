######################################################################
# 📌 04 – pandas: מדריך מלא לדאטא אנליסט (עם דוגמאות רצות)
#
# מה תקבל כאן:
#  1) מבוא ויצירת DataFrame/Series
#  2) טעינה/שמירה (CSV/Parquet/Excel) + קידוד/NA
#  3) בחירה, סינון, אינדוקס: loc / iloc / query
#  4) פעולות על עמודות: assign / astype / map / apply / vectorization
#  5) מיזוגים: merge / join / concat / merge_asof / merge_ordered
#  6) GroupBy: agg / transform / nunique / weighted avg
#  7) חלונות: rolling / expanding / cum*
#  8) תאריכים/זמן: to_datetime / dt / resample / periods
#  9) עיצוב טבלאות: pivot / pivot_table / melt / wide↔long
# 10) קטגוריות, מחרוזות, חסרים: Categorical / .str / NA / fillna / dropna
# 11) ביצועים וזיכרון: downcast / categoricals / nullable dtypes / טיפוסים יעילים
# 12) QA וולידציה: בדיקות מהירות, בדיקות ייחודיות/טווחים
# 13) אנטי-פטנים נפוצים ומה לעשות במקום
# 14) תרשימים בסיסיים עם Matplotlib (pandas.plot)
#
# דרישות (אופציונלי): pip install pandas pyarrow openpyxl matplotlib
######################################################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# כדי שיפלט יותר קומפקטי
pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)


# ==============================================================
# 1) מבוא ויצירת DataFrame/Series
# ==============================================================

# Series (עמודה בודדת עם אינדקס)
s = pd.Series([10, 20, None, 40], name="score")
print("\n[Series]\n", s)

# DataFrame (טבלה)
df = pd.DataFrame({
    "order_id":   [101, 102, 103, 104, 105, 106],
    "customer_id":[1,   1,   2,   2,   3,   1  ],
    "order_date": ["2025-07-01","2025-07-03","2025-07-03","2025-07-10","2025-07-11","2025-07-12"],
    "amount":     [120,  80,   50,  150,  300,  90],
    "coupon":     [np.nan, "SUMMER10", np.nan, np.nan, "VIP30", "SUMMER10"]
})
print("\n[DataFrame]\n", df.head())

# טיפ: columns / index / dtypes
print("\n[Columns] ", list(df.columns))
print("[Dtypes]\n", df.dtypes)


# ==============================================================
# 2) טעינה/שמירה (CSV/Parquet/Excel) + קידוד/NA
# ==============================================================

# CSV: שים לב ל-encoding (בפרויקטים בעברית לעתים 'utf-8-sig')
# df.to_csv("orders.csv", index=False, encoding="utf-8")
# df2 = pd.read_csv("orders.csv", encoding="utf-8")

# Parquet (יעיל ומהיר; דורש pyarrow/fastparquet)
# df.to_parquet("orders.parquet", index=False)
# df3 = pd.read_parquet("orders.parquet")

# Excel (דורש openpyxl ל-XLSX)
# df.to_excel("orders.xlsx", index=False)
# df4 = pd.read_excel("orders.xlsx")

# פרשנות נכון ל-NA בקלט
# df_na = pd.read_csv("file.csv", na_values=["", "NA", "null", "None"])


# ==============================================================
# 3) אינדוקס, בחירה וסינון: loc / iloc / query
# ==============================================================

# המרת order_date לתאריך
df["order_date"] = pd.to_datetime(df["order_date"])
df = df.sort_values(["customer_id","order_date"]).reset_index(drop=True)

# loc – לפי תוויות / שמות עמודות
print("\n[loc by mask]\n", df.loc[df["amount"] >= 100, ["order_id","amount"]])

# iloc – לפי מספרי אינדקס
print("\n[iloc rows 0..2, cols 0..2]\n", df.iloc[0:3, 0:3])

# query – קריא במיוחד
print("\n[query amount >= 100 & customer_id == 1]\n",
      df.query("amount >= 100 and customer_id == 1")[["order_id","amount"]])

# קביעת אינדקס
df_idx = df.set_index("order_id")
print("\n[set_index order_id]\n", df_idx.head())

# השבתה/שחזור אינדקס
df_idx = df_idx.reset_index()


# ==============================================================
# 4) פעולות על עמודות: assign / astype / map / apply / vectorization
# ==============================================================

# הוספת עמודה – assign ווקטורית
df = (df
      .assign(
          ym = df["order_date"].dt.to_period("M"),
          is_big = df["amount"].ge(120)
      ))

# map – מיפוי ערכים אחד-לאחד
coupon_map = {"SUMMER10": 0.10, "VIP30": 0.30}
df["discount"] = df["coupon"].map(coupon_map).fillna(0.0)

# vectorization – חישוב מחיר לאחר הנחה (בלי apply)
df["amount_after_disc"] = df["amount"] * (1 - df["discount"])

# apply – כשאין ברירה (יכול להיות איטי על שורות רבות)
df["size_bucket"] = df["amount"].apply(lambda x: "High" if x>=120 else ("Mid" if x>=80 else "Low"))

# astype – המרת טיפוסים (כולל nullable)
df = df.astype({"customer_id":"Int64"})  # nullable int
print("\n[assign/map/vectorize]\n", df.head())


# ==============================================================
# 5) מיזוגים: merge / join / concat / merge_asof / merge_ordered
# ==============================================================

customers = pd.DataFrame({
    "customer_id":[1,2,3],
    "name":["Dana","Avi","Chen"],
    "city":["Tel Aviv","Haifa","Jerusalem"]
})

# merge left (ברירת המחדל: inner)
df_m = df.merge(customers, on="customer_id", how="left")
print("\n[merge left customers]\n", df_m.head())

# concat – חיבור טבלאות אנכית/אופקית
part1, part2 = df.iloc[:3], df.iloc[3:]
df_concat = pd.concat([part1, part2], axis=0, ignore_index=True)

# merge_asof – צירוף לפי זמן (snap האחרון לפני האירוע)
prices = pd.DataFrame({
    "ts": pd.to_datetime(["2025-07-01 00:00","2025-07-11 00:00"]),
    "usd_ils": [3.65, 3.70]
})
df_asof = pd.merge_asof(
    df.sort_values("order_date"),
    prices.sort_values("ts"),
    left_on="order_date",
    right_on="ts",
    direction="backward"
).drop(columns=["ts"])
print("\n[merge_asof currency snap]\n", df_asof[["order_id","order_date","usd_ils"]].head())

# merge_ordered – בעיקר לסדר סדרות זמן עם join מלא ומילוי
a = pd.DataFrame({"d": pd.to_datetime(["2025-07-01","2025-07-03"]), "x":[1,3]})
b = pd.DataFrame({"d": pd.to_datetime(["2025-07-02","2025-07-03"]), "y":[2,4]})
merged_ord = pd.merge_ordered(a, b, on="d", how="outer", fill_method="ffill")
print("\n[merge_ordered]\n", merged_ord)


# ==============================================================
# 6) GroupBy: agg / transform / nunique / weighted avg
# ==============================================================

# סכום והכי גדול ללקוח
g = (df.groupby("customer_id")
       .agg(total=("amount","sum"),
            max_order=("amount","max"),
            n_orders=("order_id","count"))
       .reset_index())
print("\n[GroupBy agg]\n", g)

# transform – להחזיר באותו גודל (ליחס/אחוזים בתוך קבוצה)
df["cust_total"] = df.groupby("customer_id")["amount"].transform("sum")
df["pct_of_cust"] = df["amount"] / df["cust_total"]

# nunique – ספירת ייחודיים
unique_days = (df.groupby("customer_id")["order_date"]
                 .nunique().rename("active_days"))
print("\n[nunique active_days]\n", unique_days)

# ממוצע משוקלל (weighted avg) לדוגמה
def wavg(x, w):
    x, w = np.asarray(x), np.asarray(w)
    return (x * w).sum() / w.sum() if w.sum() else np.nan

wavg_amount = df.groupby("customer_id").apply(
    lambda sub: wavg(sub["amount"], 1 + 9*sub["is_big"].astype(int))
)
print("\n[weighted avg by customer]\n", wavg_amount)


# ==============================================================
# 7) חלונות: rolling / expanding / cum*
# ==============================================================

# הכנסות יומיות
daily = (df
         .groupby(df["order_date"].dt.date, as_index=False)["amount"]
         .sum()
         .rename(columns={"order_date":"day","amount":"daily_sales"}))
daily["day"] = pd.to_datetime(daily["day"])

# rolling 3 ימים
daily = daily.sort_values("day")
daily["avg3"] = daily["daily_sales"].rolling(3, min_periods=1).mean()
daily["run_sum"] = daily["daily_sales"].cumsum()
print("\n[rolling/cumsum]\n", daily.head())


# ==============================================================
# 8) תאריכים/זמן: to_datetime / dt / resample / periods
# ==============================================================

# עמודת תקופות (חודשים)
df["ym"] = df["order_date"].dt.to_period("M")

# resample – חייב אינדקס תאריך
ts = (df
      .set_index("order_date")
      .sort_index()
      .resample("D")["amount"]
      .sum()
      .rename("amount_per_day"))
print("\n[resample daily]\n", ts.head())

# תקופות → תאריך התחלה/סוף
df["ym_start"] = df["ym"].dt.to_timestamp(how="start")
df["ym_end"]   = df["ym"].dt.to_timestamp(how="end")


# ==============================================================
# 9) עיצוב טבלאות: pivot / pivot_table / melt
# ==============================================================

monthly = (df.groupby(["ym","customer_id"], as_index=False)["amount"]
             .sum()
             .rename(columns={"amount":"sum_amount"}))
pv = monthly.pivot(index="ym", columns="customer_id", values="sum_amount").fillna(0)
pv["total"] = pv.sum(axis=1)
print("\n[pivot monthly]\n", pv.head())

# pivot_table (עם aggfunc)
pv2 = monthly.pivot_table(index="ym", columns="customer_id", values="sum_amount",
                          aggfunc="sum", fill_value=0)

# melt – מעבר לרוחב→אורך
unpivot = pv.reset_index().melt(id_vars=["ym"], var_name="customer_id", value_name="amount")
print("\n[melt back to long]\n", unpivot.head())


# ==============================================================
# 10) קטגוריות, מחרוזות, חסרים
# ==============================================================

# Categorical – חיסכון בזיכרון + סדר קטגוריות
df["segment"] = pd.Categorical(
    np.where(df["amount"]>=120, "A", np.where(df["amount"]>=80, "B", "C")),
    categories=["A","B","C"], ordered=True
)

# .str – פעולות טקסט ו-RegEx
df["coupon_provider"] = df["coupon"].fillna("").str.extract(r"([A-Z]+)")
print("\n[String extract]\n", df[["coupon","coupon_provider"]].head())

# חסרים: isna / fillna / dropna
print("\n[NA counts]\n", df.isna().sum())
df_filled = df.fillna({"coupon":"NO_COUPON"})
df_drop   = df.dropna(subset=["amount"])   # הסרה על עמודות ספציפיות


# ==============================================================
# 11) ביצועים וזיכרון: downcast / categoricals / nullable dtypes
# ==============================================================

# דוגמה להקטנת זיכרון
big = pd.DataFrame({
    "i64": pd.Series(range(0, 100000), dtype="int64"),
    "f64": pd.Series(np.random.randn(100000), dtype="float64"),
    "city": np.random.choice(["TA","HAIFA","JLM"], size=100000)
})
mem_before = big.memory_usage(deep=True).sum()

# downcast + categorical
big_opt = big.assign(
    i32 = pd.to_numeric(big["i64"], downcast="integer"),
    f32 = pd.to_numeric(big["f64"], downcast="float"),
    city = pd.Categorical(big["city"])
).drop(columns=["i64","f64"])
mem_after = big_opt.memory_usage(deep=True).sum()
print(f"\n[Memory before→after] {mem_before/1e6:.2f}MB → {mem_after/1e6:.2f}MB")

# Nullable dtypes – Int64/boolean/StringDtype
nf = pd.DataFrame({"a":[1,2,None]})
print("\n[nullable dtypes]\n", nf.astype({"a":"Int64"}).dtypes)


# ==============================================================
# 12) QA וולידציה מהירה
# ==============================================================

# ייחודיות מפתח
assert df["order_id"].is_unique, "order_id לא ייחודי!"

# טווחים/חוקים
assert (df["amount"] >= 0).all(), "amount לא יכול להיות שלילי"
# השוואת סכומים בין גרסאות
# pd.testing.assert_series_equal(s1, s2, check_names=False)


# ==============================================================
# 13) אנטי-פטנים ומה לעשות במקום
# ==============================================================

# ❌ לולאה על שורות (iterrows/apply row-wise) לפעולות פשוטות
# ✅ להשתמש בוקטוריזציה / map / where / np.select
df["flag_big"] = np.where(df["amount"] >= 150, 1, 0)

# ❌ merge בלי לבדוק כפילויות במפתחות – גורם לשיכפול שורות
# ✅ ודא key ייחודי בצד הימני/שמאלי לפי הצורך:
# assert right_df["key"].is_unique
# ✅ בדוק גודל תוצאה צפוי: after.shape ≈ expected

# ❌ שימוש ב-object לטקסטים רבים
# ✅ StringDtype או category בהתאם לשימוש:
df["coupon"] = df["coupon"].astype("string")  # או Categorical אם רשימה קטנה


# ==============================================================
# 14) תרשימים בסיסיים (דרך pandas.plot שהוא עטיפה ל-matplotlib)
# ==============================================================

# קו – מכירות יומיות
ax = daily.plot(x="day", y="daily_sales", kind="line", title="Daily Sales")
ax.set_xlabel("Day"); ax.set_ylabel("Sales"); plt.tight_layout()
# plt.show()

# עמודות – סכום לפי לקוח
g.set_index("customer_id")["total"].plot(kind="bar", title="Total Sales by Customer")
plt.tight_layout()
# plt.show()


######################################################################
# 💡 TL;DR – צ'יטשיט קצר:
# • אינדוקס: loc (תוויות), iloc (מיקום), query (קריא למורכב).
# • המרות: astype, to_datetime; עבודה עם nullable Int64/boolean/StringDtype.
# • טרנספורמציות: assign, vectorize (אל תעשו apply לשווא).
# • GroupBy: agg לסיכומים, transform להכנסת תוצאה לכל שורה בקבוצה.
# • מיזוגים: merge (on=...), merge_asof לזמן, concat לחיבור.
# • זמן: set_index(datetime) → resample/rolling; Periods ל-ym.
# • עיצוב: pivot_table + fillna, melt לחזרה לארוך.
# • ביצועים: downcast, category, הימנעו מ-object, בדקו memory_usage().
# • QA: is_unique, בדיקות טווחים, pd.testing.assert_*.
######################################################################
