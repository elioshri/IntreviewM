/**********************************************************************
* 📌 03 – SQL SERVER INTERVIEW (SPORTS PREDICTIONS)
* שאלות ראיון + פתרונות + הסברים (בעברית)
* הקובץ מניח סכמת דוגמא שכיחה:
*   dbo.Matches(match_id, league, season, match_date, home_team_id, away_team_id,
*                home_score, away_score)
*   dbo.Teams(team_id, team_name)
*   dbo.PlayerStats(match_id, team_id, player_id, minutes, goals, xg, xa, shots, on_target, yellow, red)
*   dbo.BettingOdds(match_id, bookmaker, collected_at, home_win, draw, away_win)
*   dbo.Injuries(team_id, player_id, status, reported_at, expected_return)
*
* טיפ חשוב לראיון ספורט/חיזויים:
*   - לבנות פיצ'רים "עד זמן המשחק" (ללא מידע עתידי) – להימנע מ-Leakage.
*   - להשתמש ב-Window Functions לגלגולים (form), אחוזי ניצחון, ממוצעים.
*   - לבחור את "הגרסה האחרונה לפני המשחק" של Odds/פציעות.
**********************************************************************/

----------------------------------------------------------------------
-- 🧪 Q1: נצחונות/הפסדים/תיקו לכל קבוצה בעונה (טבלת תוצאות)
-- מטרה: בסיס לסטטיסטיקה עונתית/עיתית.
----------------------------------------------------------------------

/* פתרון + הסבר:
   נייצר 3 תוצאות אפשריות לכל משחק (Home/Away/Draw) באמצעות CASE,
   ונאגד לכל קבוצה בעונה. */
WITH base AS (
  SELECT
    m.season,
    m.home_team_id AS team_id,
    CASE
      WHEN m.home_score > m.away_score THEN 1
      ELSE 0
    END AS wins,
    CASE
      WHEN m.home_score < m.away_score THEN 1
      ELSE 0
    END AS losses,
    CASE
      WHEN m.home_score = m.away_score THEN 1
      ELSE 0
    END AS draws
  FROM dbo.Matches m
  UNION ALL
  SELECT
    m.season,
    m.away_team_id,
    CASE
      WHEN m.away_score > m.home_score THEN 1 ELSE 0
    END AS wins,
    CASE
      WHEN m.away_score < m.home_score THEN 1 ELSE 0
    END AS losses,
    CASE
      WHEN m.away_score = m.home_score THEN 1 ELSE 0
    END AS draws
  FROM dbo.Matches m
)
SELECT
  season,
  t.team_name,
  SUM(wins)   AS wins,
  SUM(draws)  AS draws,
  SUM(losses) AS losses,
  (SUM(wins)*3 + SUM(draws)) AS points
FROM base b
JOIN dbo.Teams t ON t.team_id = b.team_id
GROUP BY season, t.team_name
ORDER BY season, points DESC;
-- הסבר: מאחדים Home/Away ל"פרספקטיבה של קבוצה".
-- נקודות = 3 לניצחון, 1 לתיקו.

----------------------------------------------------------------------
-- 🧪 Q2: יחס שערים וממוצע שערים למשחק לכל קבוצה
----------------------------------------------------------------------

WITH per_team AS (
  SELECT
    m.season,
    m.home_team_id AS team_id,
    m.home_score   AS goals_for,
    m.away_score   AS goals_against
  FROM dbo.Matches m
  UNION ALL
  SELECT
    m.season,
    m.away_team_id,
    m.away_score,
    m.home_score
  FROM dbo.Matches m
),
agg AS (
  SELECT
    season, team_id,
    COUNT(*) AS matches,
    SUM(goals_for) AS gf,
    SUM(goals_against) AS ga
  FROM per_team
  GROUP BY season, team_id
)
SELECT
  a.season,
  t.team_name,
  a.matches,
  a.gf, a.ga,
  CAST(a.gf - a.ga AS INT)     AS goal_diff,
  CAST(1.0*a.gf / NULLIF(a.matches,0) AS DECIMAL(6,3)) AS avg_goals_for
FROM agg a
JOIN dbo.Teams t ON t.team_id = a.team_id
ORDER BY a.season, goal_diff DESC;
-- הסבר: איחוד Home/Away ואז אגרגציה לקבוצה.

----------------------------------------------------------------------
-- 🧪 Q3: "פורם" – ממוצע נקודות ל-5 משחקים אחרונים לפני כל משחק
-- (לכל קבוצה, נכון ל- match_date; ללא דליפת מידע עתידי)
----------------------------------------------------------------------

/* רעיון:
   לכל קבוצה ולכל משחק, נחשב ממוצע נקודות מחלון של 5 משחקים קודמים בלבד. */
WITH long AS (
  SELECT
    m.match_id, m.match_date,
    m.home_team_id AS team_id,
    CASE WHEN m.home_score > m.away_score THEN 3
         WHEN m.home_score = m.away_score THEN 1
         ELSE 0 END AS points
  FROM dbo.Matches m
  UNION ALL
  SELECT
    m.match_id, m.match_date,
    m.away_team_id,
    CASE WHEN m.away_score > m.home_score THEN 3
         WHEN m.away_score = m.home_score THEN 1
         ELSE 0 END
  FROM dbo.Matches m
),
w AS (
  SELECT
    team_id, match_id, match_date, points,
    AVG(CAST(points AS DECIMAL(6,3)))
      OVER (PARTITION BY team_id
            ORDER BY match_date
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING) AS form_avg_prev5
  FROM long
)
SELECT * FROM w ORDER BY team_id, match_date;
-- הסבר: החלון מסתיים בשורה שלפני המשחק (1 PRECEDING), אז אין זליגת עתיד.

----------------------------------------------------------------------
-- 🧪 Q4: מאפיין בית/חוץ – טבלת פיצ'רים למשחק הבא
-- נייצר מדד "Home Advantage" עונתי פשוט לכל קבוצה
----------------------------------------------------------------------

/* Home Advantage = ממוצע נקודות בבית – ממוצע נקודות בחוץ (עונה). */
WITH labeled AS (
  SELECT
    m.season,
    m.home_team_id AS team_id,
    1 AS is_home,
    CASE WHEN m.home_score > m.away_score THEN 3
         WHEN m.home_score = m.away_score THEN 1
         ELSE 0 END AS pts
  FROM dbo.Matches m
  UNION ALL
  SELECT
    m.season,
    m.away_team_id,
    0,
    CASE WHEN m.away_score > m.home_score THEN 3
         WHEN m.away_score = m.home_score THEN 1
         ELSE 0 END
  FROM dbo.Matches m
),
agg AS (
  SELECT
    season, team_id,
    AVG(CASE WHEN is_home=1 THEN pts END) AS avg_home_pts,
    AVG(CASE WHEN is_home=0 THEN pts END) AS avg_away_pts
  FROM labeled
  GROUP BY season, team_id
)
SELECT
  a.season, t.team_name,
  CAST(a.avg_home_pts - a.avg_away_pts AS DECIMAL(6,3)) AS home_advantage
FROM agg a
JOIN dbo.Teams t ON t.team_id = a.team_id
ORDER BY a.season, home_advantage DESC;
-- הסבר: מדד פשוט להדגיש יתרון בית.

----------------------------------------------------------------------
-- 🧪 Q5: בחירת ה-Odds האחרונים לפני שריקת הפתיחה (ללא דליפה)
-- נניח ש-collected_at < match_date, ויש כמה עדכונים לכל משחק/בית הימורים.
----------------------------------------------------------------------

/* נבחר את הרשומה האחרונה לכל (match_id, bookmaker) לפני match_date. */
WITH last_odds AS (
  SELECT
    o.match_id, o.bookmaker, o.collected_at, o.home_win, o.draw, o.away_win,
    ROW_NUMBER() OVER (PARTITION BY o.match_id, o.bookmaker
                       ORDER BY o.collected_at DESC) AS rn
  FROM dbo.BettingOdds o
  JOIN dbo.Matches m ON m.match_id = o.match_id
  WHERE o.collected_at < m.match_date
)
SELECT match_id, bookmaker, home_win, draw, away_win
FROM last_odds
WHERE rn = 1;
-- הסבר: משתמשים ב-RN כדי לשלוף את הרשומה ה"פסימית" האחרונה בלבד.
-- טיפ: אם רוצים לאחד בין בוקי'ס – אפשר ממוצע Odds או Wisdom of the crowd.

----------------------------------------------------------------------
-- 🧪 Q6: נרמול Odds להסתברויות ומציאת ה-Margin של הבוקי
----------------------------------------------------------------------

/* הסתברות משוערת = 1/odds; אך סכום ההסתברויות > 1 בגלל מרג'ין.
   נרמל, ונחשב Margin. */
WITH o AS (
  SELECT
    match_id, bookmaker, home_win, draw, away_win,
    (1.0/home_win + 1.0/draw + 1.0/away_win) AS inv_sum
  FROM (
    -- לדוגמה משתמשים רק ב-lastOdds מתרגיל קודם – כאן מדגימים כללי
    SELECT match_id, bookmaker, home_win, draw, away_win
    FROM dbo.BettingOdds
  ) x
),
norm AS (
  SELECT
    match_id, bookmaker,
    (1.0/home_win)/inv_sum AS p_home,
    (1.0/draw)/inv_sum     AS p_draw,
    (1.0/away_win)/inv_sum AS p_away,
    inv_sum
  FROM o
)
SELECT
  match_id, bookmaker, p_home, p_draw, p_away,
  (p_home + p_draw + p_away) - 1.0 AS margin
FROM norm;
-- הסבר: אחרי נרמול, הסכום ≈ 1 + מרג'ין (תלוי בדיוק). מרג'ין>0 = עמלת בוקי.

----------------------------------------------------------------------
-- 🧪 Q7: פיצ'רים של "כושר" לפני משחק: ממוצע שערים ו-Points ל-N משחקים
-- לדוגמה N=5, נכון ל-asof_date
----------------------------------------------------------------------

DECLARE @asof_date DATE = '2025-08-01';

WITH long AS (
  SELECT m.match_id, m.match_date,
         m.home_team_id AS team_id,
         m.home_score   AS gf,
         m.away_score   AS ga,
         CASE WHEN m.home_score > m.away_score THEN 3
              WHEN m.home_score = m.away_score THEN 1 ELSE 0 END AS pts
  FROM dbo.Matches m
  UNION ALL
  SELECT m.match_id, m.match_date,
         m.away_team_id,
         m.away_score, m.home_score,
         CASE WHEN m.away_score > m.home_score THEN 3
              WHEN m.away_score = m.home_score THEN 1 ELSE 0 END
  FROM dbo.Matches m
),
h AS (
  SELECT
    team_id, match_date, gf, ga, pts,
    AVG(CAST(gf AS DECIMAL(6,3))) OVER (PARTITION BY team_id ORDER BY match_date
                                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING) AS avg_gf_prev5,
    AVG(CAST(ga AS DECIMAL(6,3))) OVER (PARTITION BY team_id ORDER BY match_date
                                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING) AS avg_ga_prev5,
    AVG(CAST(pts AS DECIMAL(6,3))) OVER (PARTITION BY team_id ORDER BY match_date
                                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING) AS avg_pts_prev5
  FROM long
  WHERE match_date < @asof_date
)
SELECT * FROM h ORDER BY team_id, match_date;
-- הסבר: חלונות "5 קודמים בלבד" – מתאים ל-features סיבתיים.

----------------------------------------------------------------------
-- 🧪 Q8: זיהוי משחקים חסרים נתוני שחקנים/פציעות (Data Quality)
----------------------------------------------------------------------

-- משחקים ללא אף רשומת PlayerStats (חשוב לניקוי דאטה לפני מודל)
SELECT m.match_id, m.match_date, ht.team_name AS home, at2.team_name AS away
FROM dbo.Matches m
LEFT JOIN dbo.PlayerStats ps ON ps.match_id = m.match_id
JOIN dbo.Teams ht ON ht.team_id = m.home_team_id
JOIN dbo.Teams at2 ON at2.team_id = m.away_team_id
GROUP BY m.match_id, m.match_date, ht.team_name, at2.team_name
HAVING COUNT(ps.player_id) = 0;

-- משחקים ללא דיווחי Injuries עד 7 ימים לפני המשחק
SELECT m.match_id, m.match_date, ht.team_name AS home, at2.team_name AS away
FROM dbo.Matches m
LEFT JOIN dbo.Injuries i
  ON i.team_id IN (m.home_team_id, m.away_team_id)
 AND i.reported_at <= DATEADD(DAY, -7, m.match_date)
GROUP BY m.match_id, m.match_date, ht.team_name, at2.team_name
HAVING COUNT(i.player_id) = 0;
-- הסבר: מבטא יכולת לזהות חוסרים ב-features.

----------------------------------------------------------------------
-- 🧪 Q9: שליפת "סגל זמין" לפי פציעות לפני משחק
----------------------------------------------------------------------

/* נניח שיש dbo.Squad(team_id, player_id) – רשימת שחקנים קבועה.
   נרצה, לכל משחק, את כמות השחקנים הפנויים (status != 'OUT') נכון ל-3 ימים לפני המשחק. */
WITH last_injury AS (
  SELECT
    i.team_id, i.player_id,
    MAX(i.reported_at) AS last_rep
  FROM dbo.Injuries i
  GROUP BY i.team_id, i.player_id
),
snap AS (
  SELECT li.team_id, li.player_id, inj.status, inj.reported_at
  FROM last_injury li
  JOIN dbo.Injuries inj
    ON inj.team_id = li.team_id AND inj.player_id = li.player_id
   AND inj.reported_at = li.last_rep
)
SELECT
  m.match_id,
  SUM(CASE WHEN s.status = 'OUT' AND s.reported_at <= DATEADD(DAY,-3,m.match_date)
           THEN 0 ELSE 1 END) AS available_players
FROM dbo.Matches m
JOIN dbo.Squad q
  ON q.team_id IN (m.home_team_id, m.away_team_id)
LEFT JOIN snap s
  ON s.team_id = q.team_id AND s.player_id = q.player_id
GROUP BY m.match_id;
-- הסבר: לוקחים סטטוס אחרון לכל שחקן (סנאפשוט), ובודקים זמינות לפני המשחק.

----------------------------------------------------------------------
-- 🧪 Q10: Top-N לכל קבוצה – 3 השחקנים התורמים ביותר לפי xG בעונה
----------------------------------------------------------------------

WITH x AS (
  SELECT
    ps.team_id, ps.player_id, SUM(ps.xg) AS total_xg
  FROM dbo.PlayerStats ps
  GROUP BY ps.team_id, ps.player_id
),
r AS (
  SELECT
    x.team_id, x.player_id, x.total_xg,
    ROW_NUMBER() OVER (PARTITION BY x.team_id ORDER BY x.total_xg DESC) AS rn
  FROM x
)
SELECT team_id, player_id, total_xg
FROM r
WHERE rn <= 3
ORDER BY team_id, total_xg DESC;
-- הסבר: דפוס Top-N לכל קבוצה עם ROW_NUMBER.

----------------------------------------------------------------------
-- 🧪 Q11: מניעה של דליפת מידע – בדיקת חיבור "עתידי" בטעות
-- הדגמת אנטי-דוגמה ותיקון
----------------------------------------------------------------------

/* אנטי-דוגמה (לא תקין): שימוש ב-Odds שנאספו אחרי match_date */
SELECT m.match_id, o.collected_at  -- ❌ זה עלול לדלוף
FROM dbo.Matches m
JOIN dbo.BettingOdds o ON o.match_id = m.match_id
WHERE o.collected_at >= m.match_date;

-- תיקון (תקין):
SELECT m.match_id, o.collected_at
FROM dbo.Matches m
JOIN dbo.BettingOdds o ON o.match_id = m.match_id
WHERE o.collected_at < m.match_date;
-- הסבר: בראיונות מחפשים מודעות לנושא Leakage. תמיד לסנן לפי זמן.

----------------------------------------------------------------------
-- 🧪 Q12: בניית "תוצאת יעד" (Label) למשחק – 1 אם בית מנצח, 0 אחרת
-- וגם גרסת רב-מעמד (Home/Draw/Away)
----------------------------------------------------------------------

-- בינארי לבית:
SELECT
  m.match_id,
  CASE WHEN m.home_score > m.away_score THEN 1 ELSE 0 END AS y_home_win
FROM dbo.Matches m;

-- רב-מעמד:
SELECT
  m.match_id,
  CASE
    WHEN m.home_score > m.away_score THEN 'HOME'
    WHEN m.home_score < m.away_score THEN 'AWAY'
    ELSE 'DRAW'
  END AS outcome
FROM dbo.Matches m;
-- הסבר: זה ה-Label לאימון/הערכת מודל. בראיון חשוב להראות פשטות/דיוק.

----------------------------------------------------------------------
-- 🧪 Q13: בניית דלתא Elo פשוטה (דמו) – הפרש Elo לפני משחק
-- נניח שיש dbo.TeamElo(team_id, as_of_date, elo)
----------------------------------------------------------------------

/* נשלוף, לכל משחק, את ערכי ה-Elo האחרונים לפני match_date לשתי הקבוצות. */
WITH h_elo AS (
  SELECT
    m.match_id, e.elo,
    ROW_NUMBER() OVER (PARTITION BY m.match_id ORDER BY e.as_of_date DESC) AS rn
  FROM dbo.Matches m
  JOIN dbo.TeamElo e
    ON e.team_id = m.home_team_id
   AND e.as_of_date < m.match_date
),
a_elo AS (
  SELECT
    m.match_id, e.elo,
    ROW_NUMBER() OVER (PARTITION BY m.match_id ORDER BY e.as_of_date DESC) AS rn
  FROM dbo.Matches m
  JOIN dbo.TeamElo e
    ON e.team_id = m.away_team_id
   AND e.as_of_date < m.match_date
)
SELECT
  m.match_id,
  h.elo AS home_elo, a.elo AS away_elo,
  CAST(h.elo - a.elo AS DECIMAL(6,1)) AS elo_delta
FROM dbo.Matches m
LEFT JOIN h_elo h ON h.match_id = m.match_id AND h.rn = 1
LEFT JOIN a_elo a ON a.match_id = m.match_id AND a.rn = 1;
-- הסבר: משתמשים ב-RN כדי לקחת את Elo האחרון "לפני" המשחק.

----------------------------------------------------------------------
-- 🧪 Q14: פיצ'ר "Head-to-Head" – תוצאות היסטוריות בין שתי הקבוצות
-- למשל 5 מפגשים אחרונים עד המשחק הנוכחי
----------------------------------------------------------------------

/* נחשב head-to-head מהעבר בלבד. */
WITH h2h AS (
  SELECT
    m1.match_id, m2.match_id AS past_id, m2.match_date,
    CASE
      WHEN m2.home_team_id = m1.home_team_id AND m2.home_score > m2.away_score THEN 1
      WHEN m2.away_team_id = m1.home_team_id AND m2.away_score > m2.home_score THEN 1
      ELSE 0
    END AS home_team_won_past
  FROM dbo.Matches m1
  JOIN dbo.Matches m2
    ON ((m2.home_team_id = m1.home_team_id AND m2.away_team_id = m1.away_team_id)
     OR (m2.home_team_id = m1.away_team_id AND m2.away_team_id = m1.home_team_id))
   AND m2.match_date < m1.match_date
),
ranked AS (
  SELECT
    match_id, past_id, match_date, home_team_won_past,
    ROW_NUMBER() OVER (PARTITION BY match_id ORDER BY match_date DESC) AS rn
  FROM h2h
)
SELECT
  match_id,
  SUM(home_team_won_past) AS home_wins_last5
FROM ranked
WHERE rn <= 5
GROUP BY match_id;
-- הסבר: סופרים ניצחונות בית ב-5 מפגשים קודמים בלבד.

----------------------------------------------------------------------
-- 🧪 Q15: QA – זיהוי כפילויות Matches לפי (league, season, date, teams)
----------------------------------------------------------------------

SELECT league, season, match_date, home_team_id, away_team_id,
       COUNT(*) AS cnt
FROM dbo.Matches
GROUP BY league, season, match_date, home_team_id, away_team_id
HAVING COUNT(*) > 1;
-- הסבר: QA טיפוסי; מונע דאבל קאונט ב-features/labels.

----------------------------------------------------------------------
-- ✅ סיכום עקרונות שהדגמנו:
-- 1) Feature Engineering עם חלונות (rolling form) ללא דליפה (<= match_date).
-- 2) בחירת snapshot "אחרון לפני משחק" ל-Odds/Elo/Injuries.
-- 3) Top-N פר קבוצה (ROW_NUMBER) ו-Head-to-Head סיבתי.
-- 4) ניקוי דאטה (חוסרים, כפילויות).
-- 5) שימוש נכון ב-CASE/COALESCE/NULLIF ו-SARGable filters לזמני ריצה טובים.
----------------------------------------------------------------------
