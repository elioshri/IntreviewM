######################################################################
# 📌 09 – Advanced Python Q&A for Data Analysts (עם הסברים בעברית)
#
# מה בפנים (שאלות דמו-מבחן + פתרונות):
#  Q1  : קריאת CSV "מלוכלך" → טיפוסים/NA/תאריכים + בדיקות QA
#  Q2  : Top-N לכל קבוצה (קבוצות ספורט) + אנטי־כפילויות
#  Q3  : Features מתגלגלים (rolling) ללא דליפת זמן (form/points)
#  Q4  : merge_asof – התאמת שער/אודס/קמפיין לפני האירוע (anti-leak)
#  Q5  : anti-join – מציאת חסרים בין fact לטבלת reference
#  Q6  : Pivot/Pivot_table + אחוזים, total ו-ריבון (quarter)
#  Q7  : weighted average, median/percentile, IQR outliers
#  Q8  : קוהורט בסיסי (retention 7/14/30 ימים) מסשנים/הזמנות
#  Q9  : A/B Test – חישוב Lift + Welch t-test ידני (mean metric)
#  Q10 : detect leakage – בדיקת רשומות עתידיות בטעות
#  Q11 : סגמנטציה מהירה עם np.select + קטגוריות (Categorical)
#  Q12 : בניית Labels לבעיית ספורט (Home/Draw/Away) + מטריקות hit@k
#  Q13 : window מתקדמים: rank dense, pct_rank, diff, pct_change
#  Q14 : יעילות: downcast, memory_usage, בדיקת shape אחרי merge
#  Q15 : תבניות-זהב (Utility): safe merge, safe asof, check unique keys
#
# דרישות: pandas, numpy (אופציונלי: pyarrow ל-Parquet)
######################################################################

import numpy as np
import pandas as pd

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 50)

# ==============================================================
# helper: יצירת דאטה דמו קבוע כדי שהשאלות ירוצו כמו במבחן
# ==============================================================

rng = np.random.default_rng(12)

# משחקים (ספורט)
matches = pd.DataFrame({
    "match_id"     : np.arange(1001, 1031),
    "match_date"   : pd.to_datetime("2025-06-01") + pd.to_timedelta(rng.integers(0, 45, 30), unit="D"),
    "home_team_id" : rng.integers(1, 6, 30),
    "away_team_id" : rng.integers(1, 6, 30),
    "home_score"   : rng.integers(0, 5, 30),
    "away_score"   : rng.integers(0, 5, 30),
})
# הבטחה שלא יהיה home==away
matches = matches[matches["home_team_id"] != matches["away_team_id"]].reset_index(drop=True)

teams = pd.DataFrame({
    "team_id"  : np.arange(1, 6),
    "team_name": ["Lions","Wolves","Eagles","Sharks","Bulls"],
})

# אודס (Odds) שנאספים לאורך זמן לפני המשחק מאותו bookmaker
odds = (
    matches[["match_id","match_date"]]
    .merge(pd.DataFrame({"bookmaker":["BK"]}), how="cross")
    .assign(
        collected_at=lambda d: d["match_date"] - pd.to_timedelta(rng.integers(1, 72, len(d)), unit="H"),
        home_win   = lambda d: np.round(rng.uniform(1.4, 3.2, len(d)), 2),
        draw       = lambda d: np.round(rng.uniform(2.5, 4.5, len(d)), 2),
        away_win   = lambda d: np.round(rng.uniform(1.6, 3.8, len(d)), 2),
    )
)
# נכפיל רשומות כדי לדמות עדכונים (ונבחר את המאוחרות ב-asof)
extra = odds.sample(frac=0.7, random_state=7).assign(collected_at=lambda d: d["collected_at"] + pd.to_timedelta(rng.integers(1, 36, len(d)), unit="H"))
odds = pd.concat([odds, extra], ignore_index=True).sort_values(["match_id","collected_at"]).reset_index(drop=True)

# המרות מכירות (עסקי) לצורך קוהורט/AB (לא ספורט)
events = pd.DataFrame({
    "user_id"  : rng.integers(1, 400, 1500),
    "event"    : rng.choice(["visit","signup","purchase"], 1500, p=[0.6,0.25,0.15]),
    "ts"       : pd.to_datetime("2025-06-01") + pd.to_timedelta(rng.integers(0, 45, 1500), unit="D"),
    "amount"   : np.round(rng.gamma(2.2, 30, 1500), 2),
    "variant"  : rng.choice(["A","B"], 1500),
})

######################################################################
# Q1: קריאת CSV "מלוכלך", המרת טיפוסים, פרשנות NA, תאריכים, QA
######################################################################

print("\n=== Q1: parse dirty CSV ===")
csv_like = """order_id,customer_id,order_date,amount
101,1,2025/07/01,120
102,1,07-03-2025,80
103, ,2025-07-03,50
104,2,2025-07-10,150
105,3,2025-07-11,300
"""

from io import StringIO
raw = pd.read_csv(StringIO(csv_like), na_values=["", " ", "NA", "null"])
# המרת תאריך חכמה: errors='coerce' יסמן שגויים כ-NaT
raw["order_date"] = pd.to_datetime(raw["order_date"], errors="coerce", dayfirst=False, infer_datetime_format=True)
# המרת מזהים ל-nullable Int64
raw = raw.astype({"order_id":"Int64", "customer_id":"Int64", "amount":"float64"})
print(raw)

# QA בסיסי
assert raw["order_id"].is_unique, "order_id לא ייחודי"
assert raw["amount"].ge(0).all(), "amount שלילי!"
print("Q1 OK – טיפוסים ו-NA במקום")

######################################################################
# Q2: Top-N לכל קבוצה + הסרת כפילויות (duplicate rows)
#    מצא 2 השחקנים/הקבוצות (כאן 'team') עם הכי הרבה ניצחונות לכל עונה/קבוצה
######################################################################

print("\n=== Q2: Top-N per group (teams) ===")
# ניצור long per team per match
long = pd.concat([
    matches.rename(columns={"home_team_id":"team_id","home_score":"gf","away_score":"ga"})[["match_id","match_date","team_id","gf","ga"]],
    matches.rename(columns={"away_team_id":"team_id","away_score":"gf","home_score":"ga"})[["match_id","match_date","team_id","gf","ga"]],
], ignore_index=True)

# ניקוד (3/1/0)
long["pts"] = np.select(
    [long["gf"]>long["ga"], long["gf"]==long["ga"]],
    [3,1], default=0
)
# Top-2 ממוצע נקודות אחרונות לחודש (דוגמה קטנה) – נתחיל באגרגציה פשוטה
per_team = long.groupby("team_id", as_index=False)["pts"].sum().rename(columns={"pts":"total_pts"})
per_team = per_team.merge(teams, left_on="team_id", right_on="team_id", how="left")

# הוספת כפילות מלאכותית כדי להדגים הסרה
per_team_dup = pd.concat([per_team, per_team.iloc[[0]]], ignore_index=True)
per_team_clean = per_team_dup.drop_duplicates(subset=["team_id"], keep="first")
ranked = per_team_clean.assign(rnk=per_team_clean["total_pts"].rank(method="first", ascending=False))
print(ranked.sort_values("rnk").head(2))

######################################################################
# Q3: Rolling Features ללא דליפה – ממוצע נקודות 5 משחקים אחרונים עד המשחק
######################################################################

print("\n=== Q3: rolling without leakage ===")
long_sorted = long.sort_values(["team_id","match_date"])
long_sorted["avg_pts_prev5"] = (
    long_sorted
    .groupby("team_id")["pts"]
    .rolling(5, min_periods=1)
    .apply(lambda s: s.shift(1).mean(), raw=False)   # shift בתוך apply → מבטיח "עד לפני"
    .reset_index(level=0, drop=True)
)
# תחליף מהיר יותר: rolling(5).mean().shift(1) בקבוצה
long_sorted["avg_pts_prev5_fast"] = (
    long_sorted
    .groupby("team_id")["pts"]
    .apply(lambda s: s.rolling(5, min_periods=1).mean().shift(1))
    .reset_index(level=0, drop=True)
)
print(long_sorted.head())

######################################################################
# Q4: merge_asof – חיבור אודס שנאספו לפני match_date (snapshot אחרון)
######################################################################

print("\n=== Q4: merge_asof odds snapshot ===")
odds_snap = (
    pd.merge_asof(
        matches.sort_values("match_date"),
        odds.sort_values("collected_at"),
        left_on="match_date", right_on="collected_at",
        by="match_id", direction="backward", tolerance=pd.Timedelta("7D")
    )
    # נשמור רק עמודות רלוונטיות
    [["match_id","match_date","home_team_id","away_team_id","bookmaker","home_win","draw","away_win","collected_at"]]
)
print(odds_snap.head())
# הסבר: direction="backward" → בוחר את הרשומה האחרונה לפני match_date לכל match_id.

######################################################################
# Q5: Anti-Join – מציאת משחקים שחסרים להם Odds snapshot
######################################################################

print("\n=== Q5: anti-join missing odds ===")
missing_odds = matches.merge(odds_snap[["match_id"]].drop_duplicates(), on="match_id", how="left", indicator=True)
missing = missing_odds[missing_odds["_merge"]=="left_only"][["match_id","match_date"]]
print(missing.head())
# שימושי ל-Data Quality – למצוא מה חסר לפני בניית פיצ'רים.

######################################################################
# Q6: Pivot → אחוזים ו-Total + רבעונים (Quarter)
######################################################################

print("\n=== Q6: pivot + percentages + quarter ===")
sales = (
    events[events["event"]=="purchase"]
    .assign(day=lambda d: d["ts"].dt.date, q=lambda d: d["ts"].dt.to_period("Q"))
)
pv = (sales.pivot_table(index="q", columns="variant", values="amount", aggfunc=["count","sum"], fill_value=0))
pv.columns = ['_'.join(map(str, c)).strip() for c in pv.columns.to_flat_index()]
pv["sum_total"] = pv.filter(like="sum_").sum(axis=1)
for v in ["A","B"]:
    pv[f"pct_count_{v}"] = 100 * pv.get(f"count_{v}", 0) / pv.filter(like="count_").sum(axis=1)
print(pv.head())

######################################################################
# Q7: Weighted avg, percentiles, IQR Outliers
######################################################################

print("\n=== Q7: weighted avg + percentiles + IQR ===")
x = np.array([10, 12, 18, 20, 200, 22, 24, 26, 28, 30])
w = np.array([1,1,1,1,1,1,1,1,1,1])
wavg = (x*w).sum() / w.sum()
q1, q3 = np.percentile(x, [25, 75])
iqr = q3 - q1
upper = q3 + 1.5*iqr
lower = q1 - 1.5*iqr
outliers = x[(x<lower) | (x>upper)]
print(f"wavg={wavg:.2f}, p25={q1}, p75={q3}, IQR={iqr}, bounds=({lower},{upper}), outliers={outliers}")

######################################################################
# Q8: קוהורט בסיסי – אחוז משתמשים שחזרו בתוך 7/14/30 ימים מהביקור הראשון
######################################################################

print("\n=== Q8: simple cohort (7/14/30-day return) ===")
visits = events[events["event"]=="visit"][["user_id","ts"]].rename(columns={"ts":"visit_ts"})
first = visits.groupby("user_id", as_index=False)["visit_ts"].min().rename(columns={"visit_ts":"first_ts"})
ret = visits.merge(first, on="user_id", how="left")
ret["delta"] = (ret["visit_ts"] - ret["first_ts"]).dt.days
cohort = ret.groupby("user_id", as_index=False)["delta"].min()  # הביקור הראשון הוא 0
# האם חזר בתוך חלון
def within(d, k): return (ret["delta"].between(1, k)).groupby(ret["user_id"]).any().mean()
print({"ret7": within(ret, 7), "ret14": within(ret, 14), "ret30": within(ret, 30)})

######################################################################
# Q9: A/B – Lift + Welch t-test ידני על ממוצע purchase amount
######################################################################

print("\n=== Q9: AB (Welch t-test) ===")
purch = events[events["event"]=="purchase"][["variant","amount"]]
A = purch.loc[purch["variant"]=="A","amount"].to_numpy()
B = purch.loc[purch["variant"]=="B","amount"].to_numpy()

lift = (B.mean() - A.mean()) / max(A.mean(), 1e-9)
# Welch t
def welch_t(a, b):
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(ddof=1), b.var(ddof=1)
    na, nb = len(a), len(b)
    t = (ma-mb) / np.sqrt(va/na + vb/nb)
    # df (Welch–Satterthwaite)
    df = (va/na + vb/nb)**2 / ( (va**2)/((na**2)*(na-1)) + (vb**2)/((nb**2)*(nb-1)) )
    return t, df

t_stat, df = welch_t(A, B)
print(f"lift={lift:.3%}, t={t_stat:.3f}, df≈{df:.1f}")
# (\* להערכת p-value דרוש cdf של t; כאן מספיק t ו-DF להצגה במבחן)

######################################################################
# Q10: detect leakage – האם יש אודס שנאספו אחרי match_date?
######################################################################

print("\n=== Q10: leakage check ===")
leak = odds.merge(matches[["match_id","match_date"]], on="match_id", how="left")
has_leak = (leak["collected_at"] >= leak["match_date"]).any()
print("leakage?", has_leak)
# במבחן: להראות שגם בצירופים משתמשים תמיד direction='backward' ו-tolerance.

######################################################################
# Q11: סגמנטציה מהירה np.select + Categorical (ליעילות זיכרון)
######################################################################

print("\n=== Q11: segmentation ===")
amounts = pd.Series(np.round(rng.normal(120, 50, 20).clip(5),2), name="amount")
bins = np.select(
    [amounts>=180, amounts>=120, amounts>=80],
    ["VIP","A","B"], default="C"
)
seg = pd.Categorical(bins, categories=["VIP","A","B","C"], ordered=True)
print(pd.DataFrame({"amount":amounts, "segment":seg}).head())

######################################################################
# Q12: Labels לספורט + hit@k – האם ההימור על בית נכנס בטופ K הסתברויות
######################################################################

print("\n=== Q12: sports labels + hit@k ===")
labels = matches[["match_id","home_score","away_score"]].assign(
    label = lambda d: np.select(
        [d["home_score"]>d["away_score"], d["home_score"]<d["away_score"]],
        ["HOME","AWAY"], default="DRAW"
    )
)
# הסתברויות מנורמלות מאודס (דמו): p ~ 1/odds, normalize
snap = odds_snap.dropna(subset=["home_win","draw","away_win"]).copy()
inv_sum = (1/snap["home_win"] + 1/snap["draw"] + 1/snap["away_win"])
snap["p_home"] = (1/snap["home_win"]) / inv_sum
snap["p_draw"] = (1/snap["draw"])     / inv_sum
snap["p_away"] = (1/snap["away_win"]) / inv_sum

# hit@1: קטגוריה עם p הכי גבוה תואמת ל-label?
pred = snap[["match_id","p_home","p_draw","p_away"]].merge(labels[["match_id","label"]], on="match_id", how="inner")
pred["argmax"] = pred[["p_home","p_draw","p_away"]].idxmax(axis=1).str.replace("p_","").str.upper()
hit1 = (pred["argmax"] == pred["label"]).mean()
# hit@2 (האם ה-label בתוך 2 ההסתברויות הגבוהות)
top2 = pred[["p_home","p_draw","p_away"]].apply(lambda r: r.sort_values(ascending=False).index[:2], axis=1).apply(lambda idx: set(idx.str.replace("p_","").str.upper()))
hit2 = np.mean([pred.iloc[i]["label"] in s for i, s in enumerate(top2)])
print({"hit@1": round(hit1,3), "hit@2": round(hit2,3)})

######################################################################
# Q13: Window מתקדמים – rank dense, pct_rank, diff, pct_change
######################################################################

print("\n=== Q13: window extras ===")
sales_daily = (
    events[events["event"]=="purchase"][["ts","amount"]]
    .assign(day=lambda d: d["ts"].dt.date)
    .groupby("day", as_index=False)["amount"].sum()
    .sort_values("day")
)
sales_daily["rank_dense"] = sales_daily["amount"].rank(method="dense", ascending=False)
sales_daily["pct_rank"]   = sales_daily["amount"].rank(pct=True)
sales_daily["diff"]       = sales_daily["amount"].diff()
sales_daily["pct_change"] = sales_daily["amount"].pct_change()
print(sales_daily.head(10))

######################################################################
# Q14: יעילות ומדדים – downcast, memory, shape אחרי merge
######################################################################

print("\n=== Q14: efficiency & shape ===")
big = pd.DataFrame({
    "i64": pd.Series(np.arange(0, 200000), dtype="int64"),
    "f64": pd.Series(rng.normal(0, 1, 200000), dtype="float64"),
    "key": pd.Series(rng.integers(0, 200000, 200000), dtype="int64"),
})
mem_before = big.memory_usage(deep=True).sum()
big_opt = big.assign(
    i32 = pd.to_numeric(big["i64"], downcast="integer"),
    f32 = pd.to_numeric(big["f64"], downcast="float")
).drop(columns=["i64","f64"])
mem_after = big_opt.memory_usage(deep=True).sum()
print(f"memory MB: {mem_before/1e6:.2f} → {mem_after/1e6:.2f}")

# shape אחרי merge – בדוק שאין קרוס-ג'וין/כפילויות מפתחות
left = pd.DataFrame({"key":[1,2,3], "x":[10,20,30]})
right= pd.DataFrame({"key":[1,2,2,4], "y":[100,200,250,400]})
merged = left.merge(right, on="key", how="left")
print("shapes:", left.shape, right.shape, merged.shape)  # (3,2), (4,2), (4,2) → כפילות key=2 בצד ימין
# פתרון: דה-דופ לצד ימין לפי חוקי עסק (agg או drop_duplicates)

######################################################################
# Q15: Utility תבניות זהב – שימושיות בכל מבחן/פרויקט
######################################################################

print("\n=== Q15: utilities ===")

def check_unique(df, cols):
    """מאשר שמפתחות ייחודיים; אחרת מדפיס דוגמאות שגיאה."""
    ok = df.duplicated(subset=cols, keep=False).sum() == 0
    if not ok:
        print("⚠️ duplicates in keys", cols)
        print(df[df.duplicated(subset=cols, keep=False)].head())
    return ok

def safe_merge(left, right, on, how="left", check_right_unique=False):
    """מיזוג עם בדיקות צורה/ייחודיות – מצמצם תקלות מבחן."""
    if check_right_unique:
        assert right[on].is_unique, f"Right key {on} not unique!"
    before = len(left)
    out = left.merge(right, on=on, how=how)
    after = len(out)
    if how in ("left","inner") and after < before:
        print(f"⚠️ rows dropped: {before-after}")
    return out

def safe_asof(left, right, left_on, right_on, by=None, tolerance="7D", direction="backward"):
    """עטיפה ל-asof עם ברירות מחדל בטוחות נגד דליפה."""
    return pd.merge_asof(
        left.sort_values(left_on),
        right.sort_values(right_on),
        left_on=left_on, right_on=right_on, by=by,
        tolerance=pd.Timedelta(tolerance), direction=direction
    )

# דוגמאות שימוש:
print("unique match_id?", check_unique(matches, ["match_id"]))
ex = safe_merge(matches, teams.rename(columns={"team_id":"home_team_id","team_name":"home_name"}), on="home_team_id", how="left")
snap2 = safe_asof(matches, odds, "match_date", "collected_at", by="match_id")

print("\n✅ סוף – יש לך בנק שאלות–פתרונות כמו במבחן, עם דגש על מניעת דליפה, חלונות, הצטרפויות, KPI, וקוהורטים.")
