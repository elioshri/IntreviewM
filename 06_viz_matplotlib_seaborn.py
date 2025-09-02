######################################################################
# 📌 06 – ויזואליזציה לדאטא אנליסט: Matplotlib + Seaborn (מלא ומעשי)
#
# מה יש כאן:
#  1) סטאפ ומבנה בסיסי של פיגור/צירים
#  2) גרפים נפוצים (קו, עמודות, פיזור, היסטוגרמה)
#  3) Subplots גריד + שיתוף צירים
#  4) ציר משני / שתי סקאלות (twinx)
#  5) תאריכים וסדרות זמן
#  6) עיצוב: כותרות, מקרא, טיקים, תוויות, צבעים, פריסה, שמירה לקובץ
#  7) Seaborn: התפלגויות, קשרים, קטגוריאלי, heatmap, FacetGrid
#  8) טיפים לאחידות, נגישות וצ'קליסט לפני שמציגים
#
# תלות: pip install matplotlib seaborn pandas numpy
######################################################################

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# סטייל בסיסי נעים; אפשר לנסות גם 'whitegrid'/'darkgrid'
sns.set_theme(context="notebook", style="whitegrid", font_scale=1.1)

# נתוני דמה נוחים לדוגמאות:
rng = np.random.default_rng(42)
dates = pd.date_range("2025-07-01", periods=14, freq="D")
sales = pd.Series(rng.normal(100, 20, len(dates)).clip(20), index=dates, name="sales")
cust = pd.DataFrame({
    "customer_id": np.repeat([1,2,3,4], 20),
    "amount": rng.normal(120, 40, 80).clip(5),
    "channel": rng.choice(["Web","Store","Partner"], 80, p=[0.5,0.35,0.15]),
    "city": rng.choice(["TA","Haifa","JLM"], 80)
})
cust["date"] = pd.to_datetime("2025-07-01") + pd.to_timedelta(rng.integers(0, 14, 80), unit="D")

######################################################################
# 1) מבנה בסיסי – Figure & Axes (חשוב לכתיבה נקייה וניתנת לשחזור)
######################################################################

# דפוס מומלץ: fig, ax = plt.subplots()
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(sales.index, sales.values, marker="o")
ax.set_title("Daily Sales")
ax.set_xlabel("Date")
ax.set_ylabel("Sales")
fig.autofmt_xdate()         # הטיית תאריכים
fig.tight_layout()          # פריסה אוטומטית
# fig.savefig("daily_sales.png", dpi=150)
plt.close(fig)

######################################################################
# 2) גרפים נפוצים
######################################################################

# קו
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(sales.index, sales, linewidth=2)
ax.set(title="Line Plot", xlabel="Date", ylabel="Sales")
fig.tight_layout(); plt.close(fig)

# עמודות
by_day = sales.resample("D").sum()
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(by_day.index.astype(str), by_day.values)
ax.set(title="Bar Chart (Daily)", xlabel="Day", ylabel="Sales")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout(); plt.close(fig)

# פיזור (scatter)
fig, ax = plt.subplots(figsize=(6, 4))
x = rng.normal(50, 10, 100)
y = x * 1.5 + rng.normal(0, 8, 100)
ax.scatter(x, y, alpha=0.7)
ax.set(title="Scatter", xlabel="Feature X", ylabel="Feature Y")
fig.tight_layout(); plt.close(fig)

# היסטוגרמה + KDE עם Seaborn
fig, ax = plt.subplots(figsize=(6, 4))
sns.histplot(cust["amount"], kde=True, bins=20, ax=ax)
ax.set(title="Distribution of Amount", xlabel="Amount", ylabel="Count")
fig.tight_layout(); plt.close(fig)

######################################################################
# 3) Subplots גריד + שיתוף צירים
######################################################################

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(9, 6), sharex=False, sharey=False)
axes = axes.ravel()

axes[0].plot(sales.index, sales, marker="o"); axes[0].set_title("Line")
axes[1].bar(by_day.index.astype(str), by_day.values); axes[1].set_title("Bar")
axes[1].tick_params(axis="x", rotation=45)
axes[2].hist(cust["amount"], bins=15); axes[2].set_title("Hist")
axes[3].scatter(x, y, alpha=0.7); axes[3].set_title("Scatter")

fig.suptitle("Common Plots", y=1.02, fontsize=14)
fig.tight_layout(); plt.close(fig)

######################################################################
# 4) שתי סקאלות – ציר משני (twinx)
######################################################################

# דוגמה: מכירות יומיות מול ממוצע נע
avg7 = sales.rolling(7, min_periods=1).mean()

fig, ax1 = plt.subplots(figsize=(7, 4))
ax1.plot(sales.index, sales, label="Sales", linewidth=1.8)
ax1.set_xlabel("Date"); ax1.set_ylabel("Sales")

ax2 = ax1.twinx()
ax2.plot(avg7.index, avg7, linestyle="--", label="7-day MA", color="tab:orange")
ax2.set_ylabel("7-day MA")

# מקרא משולב
lines = ax1.get_lines() + ax2.get_lines()
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="upper left")

fig.tight_layout(); plt.close(fig)

######################################################################
# 5) עבודה עם תאריכים וסדרות זמן
######################################################################

# resample יומי → שבועי
weekly = sales.resample("W").sum()

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(sales.index, sales, alpha=0.6, label="Daily")
ax.plot(weekly.index, weekly, marker="o", label="Weekly Sum")
ax.set(title="Time Series", xlabel="Date", ylabel="Sales")
ax.legend()
fig.autofmt_xdate(); fig.tight_layout(); plt.close(fig)

######################################################################
# 6) עיצוב וניקיון: כותרות, טיקים, אנוטציות, צבעים, שמירה
######################################################################

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(sales.index, sales, color="tab:blue")
peak_idx = sales.idxmax()
ax.scatter([peak_idx], [sales.max()], color="tab:red", zorder=3)
ax.annotate(f"Peak: {sales.max():.0f}",
            xy=(peak_idx, sales.max()),
            xytext=(10, 15), textcoords="offset points",
            arrowprops=dict(arrowstyle="->", lw=1))
# גריד/טיקים
ax.grid(True, axis="y", alpha=0.2)
ax.tick_params(axis="x", rotation=45)
ax.set(title="Annotations & Clean Axes", xlabel="Date", ylabel="Sales")
fig.tight_layout()
# שמירה עם DPI ורקע שקוף/לא שקוף
# fig.savefig("nice_plot.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)

######################################################################
# 7) Seaborn – מהיר לשימוש עם DataFrames
######################################################################

# a) קשרים: regplot / lmplot (רגרסיה)
tips = pd.DataFrame({
    "total_bill": rng.normal(30, 10, 200).clip(5),
    "tip": rng.normal(5, 2, 200).clip(0.5),
    "sex": rng.choice(["Male","Female"], 200),
    "smoker": rng.choice(["Yes","No"], 200, p=[0.3, 0.7]),
    "day": rng.choice(["Thur","Fri","Sat","Sun"], 200),
    "size": rng.integers(1,6,200)
})
fig, ax = plt.subplots(figsize=(6, 4))
sns.regplot(data=tips, x="total_bill", y="tip", ax=ax, scatter_kws={"alpha":0.5})
ax.set_title("Regplot (linear fit)"); fig.tight_layout(); plt.close(fig)

# b) pairplot – סקירה מהירה של קשרים/התפלגויות
g = sns.pairplot(tips[["total_bill","tip","size"]])
plt.tight_layout(); plt.close(g.fig)

# c) קטגוריאלי: box / violin / bar / catplot
fig, ax = plt.subplots(figsize=(6, 4))
sns.boxplot(data=cust, x="channel", y="amount", ax=ax)
ax.set_title("Boxplot by Channel"); fig.tight_layout(); plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 4))
sns.violinplot(data=cust, x="channel", y="amount", cut=0, inner="quartile", ax=ax)
ax.set_title("Violin by Channel"); fig.tight_layout(); plt.close(fig)

# d) heatmap – מטריצת קורלציה
corr = cust[["amount"]].join(
    pd.get_dummies(cust[["channel","city"]], drop_first=True)
).corr()
fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(corr, annot=False, cmap="coolwarm", center=0, ax=ax)
ax.set_title("Correlation Heatmap"); fig.tight_layout(); plt.close(fig)

# e) FacetGrid – השוואה בין חיתוכים
g = sns.FacetGrid(cust, col="city", row="channel", margin_titles=True, height=2.5)
g.map_dataframe(sns.histplot, x="amount", bins=15)
g.fig.subplots_adjust(top=0.92); g.fig.suptitle("Amount by City × Channel")
plt.close(g.fig)

######################################################################
# 8) טיפים פרקטיים + נגישות + צ'קליסט
######################################################################
"""
טיפים:
• בנו גרף על ציר אחד (Axes) – ואספו נתונים דומים לאותו ציר, כדי לא ליצור עומס.
• תעדפו fig, ax = plt.subplots() על plt.plot ישיר – יותר שליטה.
• מיתוג צבעים עקבי: אותה ישות = אותו צבע בכל הגרפים.
• אל תגזימו במקרא; כאשר ברור – אפשר תוויות ישירות על הקווים (annotate).
• בייצוא: bbox_inches='tight', dpi=150–300 למצגות/דוחות.

נגישות:
• השתמשו בפלטות ידידותיות לעיוורי צבעים (למשל sns.color_palette("colorblind")).
• הגדילו font_scale ב-Seaborn/rcParams בכותרות/טיקים לגרפים צפופים.
• בדקו קונטרסט בין טקסט לרקע; הימנעו מטקסט קטן/ממורח.

צ'קליסט לפני שליחה:
[ ] כותרת ברורה + צירי X/Y מתויגים
[ ] יחידות מדידה הובהרו (₪, %, שעות, ...)
[ ] טווחי תאריכים/פילטרים מצוינים בטקסט/כותרת
[ ] מקרא נחוץ? אם כן, לא מסתיר נתונים
[ ] טיקים קריאים (סיבוב/פורמט תאריך מתאים)
[ ] שמירה ל-PNG/SVG באיכות מתאימה
"""
######################################################################

# דוגמה קצרה לפלטות וצבעים קבועים:
palette = sns.color_palette("colorblind")
fig, ax = plt.subplots(figsize=(7, 4))
for i, city in enumerate(cust["city"].unique()):
    s = cust[cust["city"] == city].groupby("date")["amount"].mean()
    ax.plot(s.index, s.values, marker="o", label=city, linewidth=2, color=palette[i])
ax.set(title="Avg Amount by City (Daily)", xlabel="Date", ylabel="Amount")
ax.legend()
fig.autofmt_xdate(); fig.tight_layout(); plt.close(fig)

# סוף. תרגיש חופשי להעתיק חלקים רלוונטיים לכל מצגת/דוח.
