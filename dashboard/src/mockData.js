// Static fallback data used when the live API is unreachable
// (e.g. Render free-tier cold start). Keeps the dashboard fully populated.

export const MOCK = {
  health: {
    status: "ok",
    models_loaded: true,
    mock: true,
  },

  overview: {
    dau: 1284,
    mau: 18650,
    avg_session_secs: 342,
    high_churn_count: 27,
  },

  dau: [
    { event_date: "2026-06-06", dau: 1190, total_events: 8420, total_sessions: 1510 },
    { event_date: "2026-06-07", dau: 1225, total_events: 8710, total_sessions: 1562 },
    { event_date: "2026-06-08", dau: 1180, total_events: 8120, total_sessions: 1488 },
    { event_date: "2026-06-09", dau: 1260, total_events: 8990, total_sessions: 1601 },
    { event_date: "2026-06-10", dau: 1302, total_events: 9210, total_sessions: 1655 },
    { event_date: "2026-06-11", dau: 1248, total_events: 8850, total_sessions: 1572 },
    { event_date: "2026-06-12", dau: 1271, total_events: 9105, total_sessions: 1610 },
    { event_date: "2026-06-13", dau: 1284, total_events: 9230, total_sessions: 1634 },
  ],

  segments: [
    { segment: "regular", user_count: 8200, pct: 44.0, avg_events: 5.4, avg_sessions: 2.1 },
    { segment: "power_user", user_count: 2750, pct: 14.7, avg_events: 12.8, avg_sessions: 4.6 },
    { segment: "at_risk", user_count: 1980, pct: 10.6, avg_events: 1.9, avg_sessions: 0.8 },
    { segment: "new_user", user_count: 3920, pct: 21.0, avg_events: 3.2, avg_sessions: 1.4 },
    { segment: "dormant", user_count: 1800, pct: 9.7, avg_events: 0.4, avg_sessions: 0.2 },
  ],

  atRisk: Array.from({ length: 30 }, (_, i) => {
    const segments = ["regular", "power_user", "at_risk", "new_user", "dormant"];
    const plans = ["free", "starter", "pro", "enterprise"];
    const score = +(Math.max(0, Math.min(1, 0.95 - i * 0.027 + (i % 3) * 0.01))).toFixed(2);
    const risk = score >= 0.6 ? "high" : score >= 0.3 ? "medium" : "low";
    return {
      user_id: `usr_${1000 + i}`,
      company: `Company ${String.fromCharCode(65 + (i % 26))}${i}`,
      segment: segments[i % segments.length],
      plan: plans[i % plans.length],
      days_inactive: 1 + ((i * 3) % 14),
      churn_score: score,
      churn_risk: risk,
    };
  }),
};
