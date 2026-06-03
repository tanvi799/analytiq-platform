import { useState, useEffect, useCallback, createContext, useContext, useRef } from "react";
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const API = "https://analytiq-api.onrender.com";
const ThemeCtx = createContext();
const useTheme = () => useContext(ThemeCtx);

// ── Theme ─────────────────────────────────────────────────────────────────────
function ThemeProvider({ children }) {
  const [dark, setDark] = useState(true);
  const t = {
    dark, toggle: () => setDark(d => !d),
    bg: dark ? "#0B0B14" : "#F0F2F7",
    surface: dark ? "rgba(255,255,255,0.04)" : "#FFFFFF",
    surfaceHov: dark ? "rgba(255,255,255,0.07)" : "#F8F9FC",
    border: dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.09)",
    borderHov: dark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.18)",
    text: dark ? "#E8E8FF" : "#0D0D1A",
    textSub: dark ? "rgba(180,180,230,0.55)" : "rgba(0,0,40,0.55)",
    textMuted: dark ? "rgba(140,140,200,0.35)" : "rgba(0,0,40,0.35)",
    sidebar: dark ? "#0D0D18" : "#FAFBFD",
    sidebarBdr: dark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.08)",
    header: dark ? "rgba(11,11,20,0.9)" : "rgba(240,242,247,0.93)",
    chart: dark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.05)",
    input: dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)",
    inputBdr: dark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.12)",
    navActive: dark ? "rgba(99,102,241,0.18)" : "rgba(99,102,241,0.1)",
    navActiveT: dark ? "#ffffff" : "#000000",
    tableBdr: dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.06)",
    codeBg: dark ? "rgba(16,185,129,0.06)" : "rgba(16,185,129,0.06)",
    statusBg: dark ? "rgba(16,185,129,0.06)" : "rgba(16,185,129,0.04)",
    statusBdr: dark ? "rgba(16,185,129,0.2)" : "rgba(16,185,129,0.25)",
    selectBg: dark ? "#13131F" : "#FFFFFF",
    glow: dark ? "0 0 40px rgba(99,102,241,0.07)" : "0 4px 20px rgba(0,0,0,0.06)",
    ttBg: dark ? "#0E0E1C" : "#FFFFFF",
    ttBdr: dark ? "rgba(99,102,241,0.25)" : "rgba(0,0,0,0.1)",
    ttShadow: dark ? "0 16px 48px rgba(0,0,0,0.6)" : "0 8px 32px rgba(0,0,0,0.1)",
  };
  return <ThemeCtx.Provider value={t}>{children}</ThemeCtx.Provider>;
}

const C = {
  indigo: "#6366F1",
  emerald: "#10B981",
  amber: "#F59E0B",
  rose: "#F43F5E",
  sky: "#38BDF8",
  violet: "#8B5CF6",
  slate: "#64748B",
};

const SEG_COLORS = {
  regular: C.indigo, power_user: C.emerald,
  at_risk: C.amber, new_user: C.sky, dormant: C.slate,
};

const RISK = {
  high: { bg: "rgba(244,63,94,0.08)", border: "rgba(244,63,94,0.25)", text: "#F43F5E" },
  medium: { bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.25)", text: "#F59E0B" },
  low: { bg: "rgba(16,185,129,0.08)", border: "rgba(16,185,129,0.25)", text: "#10B981" },
};

// ── Responsive hook ───────────────────────────────────────────────────────────
function useResponsive() {
  const [w, setW] = useState(window.innerWidth);
  useEffect(() => {
    const fn = () => setW(window.innerWidth);
    window.addEventListener("resize", fn);
    return () => window.removeEventListener("resize", fn);
  }, []);
  return { isMobile: w < 640, isTablet: w < 1024, width: w };
}

// ── Fetch ─────────────────────────────────────────────────────────────────────
function useFetch(path, interval = 0) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpd, setLastUpd] = useState(null);
  const refetch = useCallback(() => {
    fetch(`${API}${path}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); setLastUpd(new Date()); })
      .catch(() => setLoading(false));
  }, [path]);
  useEffect(() => {
    refetch();
    if (interval > 0) { const id = setInterval(refetch, interval); return () => clearInterval(id); }
  }, [refetch, interval]);
  return { data, loading, lastUpd, refetch };
}

// ── Animated counter ──────────────────────────────────────────────────────────
function Num({ v, suffix = "" }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (v == null) return;
    const target = parseFloat(v), steps = 50; let i = 0;
    const ease = t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    const tm = setInterval(() => {
      i++; setN(parseFloat((target * ease(i / steps)).toFixed(1)));
      if (i >= steps) clearInterval(tm);
    }, 16);
    return () => clearInterval(tm);
  }, [v]);
  return <span>{Number.isInteger(n) ? n.toLocaleString() : n}{suffix}</span>;
}

// ── Tooltip ───────────────────────────────────────────────────────────────────
function Tip({ active, payload, label }) {
  const t = useTheme();
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: t.ttBg, border: `1px solid ${t.ttBdr}`, borderRadius: 10, padding: "10px 14px", boxShadow: t.ttShadow }}>
      <p style={{ fontSize: 10, color: t.textMuted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</p>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
          <div style={{ width: 6, height: 6, borderRadius: 2, background: p.color || p.fill || C.indigo }} />
          <span style={{ fontSize: 11, color: t.textSub }}>{p.name}:</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: t.text }}>{typeof p.value === "number" ? p.value.toLocaleString() : p.value}</span>
        </div>
      ))}
    </div>
  );
}

// ── Card ──────────────────────────────────────────────────────────────────────
function Card({ children, style = {} }) {
  const t = useTheme();
  return (
    <div style={{ background: t.surface, border: `1px solid ${t.border}`, borderRadius: 14, padding: "20px 22px", boxShadow: t.glow, ...style }}>
      {children}
    </div>
  );
}

// ── Section header ────────────────────────────────────────────────────────────
function SH({ title, sub, right }) {
  const t = useTheme();
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 18 }}>
      <div>
        <p style={{ fontSize: 13, fontWeight: 600, color: t.text, letterSpacing: "-0.01em" }}>{title}</p>
        {sub && <p style={{ fontSize: 11, color: t.textMuted, marginTop: 2 }}>{sub}</p>}
      </div>
      {right}
    </div>
  );
}

// ── Badge ─────────────────────────────────────────────────────────────────────
function Badge({ label, color }) {
  return <span style={{ fontSize: 10, padding: "2px 9px", borderRadius: 20, background: color + "16", color, fontWeight: 600, border: `1px solid ${color}28`, letterSpacing: "0.04em" }}>{label}</span>;
}

// ── Glow dot ──────────────────────────────────────────────────────────────────
function GlowDot({ color, size = 7, pulse = false }) {
  return <div style={{ width: size, height: size, borderRadius: "50%", background: color, boxShadow: `0 0 ${size + 2}px ${color}`, flexShrink: 0, animation: pulse ? "pulse 2s infinite" : "none" }} />;
}

// ── Sparkline ─────────────────────────────────────────────────────────────────
function Spark({ data, k, color }) {
  return (
    <ResponsiveContainer width="100%" height={36}>
      <LineChart data={data}>
        <Line type="monotone" dataKey={k} stroke={color} strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── KPI Card ──────────────────────────────────────────────────────────────────
function KPI({ label, value, suffix = "", color, spark, sparkKey, sub, delta, deltaUp }) {
  const t = useTheme();
  const [hov, setHov] = useState(false);
  return (
    <div onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{
      background: hov ? t.surfaceHov : t.surface,
      border: `1px solid ${hov ? t.borderHov : t.border}`,
      borderRadius: 14, padding: "18px 20px", transition: "all 0.2s", cursor: "default",
      position: "relative", overflow: "hidden", boxShadow: hov ? `0 8px 28px rgba(0,0,0,0.2)` : t.glow,
    }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg,${color},${color}00)` }} />
      <div style={{ position: "absolute", top: -20, right: -10, width: 80, height: 80, borderRadius: "50%", background: color, opacity: 0.04, filter: "blur(24px)", pointerEvents: "none" }} />
      <p style={{ fontSize: 10, fontWeight: 600, color: t.textMuted, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>{label}</p>
      <p style={{ fontSize: 28, fontWeight: 700, color: t.text, letterSpacing: "-0.03em", lineHeight: 1 }}>
        {value == null ? <span style={{ opacity: 0.2 }}>—</span> : <Num v={value} suffix={suffix} />}
      </p>
      {sub && <p style={{ fontSize: 11, color: t.textMuted, marginTop: 3 }}>{sub}</p>}
      {delta && (
        <span style={{ display: "inline-block", marginTop: 7, fontSize: 10, color: deltaUp ? C.emerald : C.rose, background: deltaUp ? "rgba(16,185,129,0.1)" : "rgba(244,63,94,0.1)", padding: "2px 7px", borderRadius: 20, fontWeight: 600, border: `1px solid ${deltaUp ? C.emerald : C.rose}28` }}>
          {deltaUp ? "+" : ""}{delta}
        </span>
      )}
      {spark && <div style={{ marginTop: 10, opacity: 0.65 }}><Spark data={spark} k={sparkKey} color={color} /></div>}
    </div>
  );
}

// ── Icons ─────────────────────────────────────────────────────────────────────
const I = {
  overview: () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1" y="1" width="5" height="5" rx="1.5" stroke="currentColor" strokeWidth="1.3" /><rect x="8" y="1" width="5" height="5" rx="1.5" stroke="currentColor" strokeWidth="1.3" /><rect x="1" y="8" width="5" height="5" rx="1.5" stroke="currentColor" strokeWidth="1.3" /><rect x="8" y="8" width="5" height="5" rx="1.5" stroke="currentColor" strokeWidth="1.3" /></svg>,
  churn: () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.3" /><path d="M7 4v3.2l2 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" /></svg>,
  seg: () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1L13 4v6L7 13 1 10V4L7 1z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /></svg>,
  events: () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 10l3-3.5 3 2.5 3-5 3-2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  pipeline: () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 4h10M2 7h10M2 10h10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" /><circle cx="5" cy="4" r="1.5" fill="currentColor" /><circle cx="9" cy="7" r="1.5" fill="currentColor" /><circle cx="6" cy="10" r="1.5" fill="currentColor" /></svg>,
  health: () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 7h2.5l1.5-4 3 8 2-4H13" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  sun: () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><circle cx="6.5" cy="6.5" r="2.5" stroke="currentColor" strokeWidth="1.3" /><path d="M6.5 1v1.5M6.5 10.5V12M1 6.5h1.5M10.5 6.5H12M2.64 2.64l1.06 1.06M9.3 9.3l1.06 1.06M2.64 10.36l1.06-1.06M9.3 3.7l1.06-1.06" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" /></svg>,
  moon: () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M11.5 7A5 5 0 016 1.5a5 5 0 100 10A5 5 0 0011.5 7z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /></svg>,
  refresh: () => <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M10 6A4 4 0 112 6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /><path d="M10 2.5V6H6.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  menu: () => <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>,
  close: () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>,
  drag: () => <svg width="12" height="16" viewBox="0 0 12 16" fill="none"><circle cx="4" cy="4" r="1.2" fill="currentColor" opacity="0.4" /><circle cx="8" cy="4" r="1.2" fill="currentColor" opacity="0.4" /><circle cx="4" cy="8" r="1.2" fill="currentColor" opacity="0.4" /><circle cx="8" cy="8" r="1.2" fill="currentColor" opacity="0.4" /><circle cx="4" cy="12" r="1.2" fill="currentColor" opacity="0.4" /><circle cx="8" cy="12" r="1.2" fill="currentColor" opacity="0.4" /></svg>,
};

const NAV = [
  { id: "overview", label: "Overview", Ic: I.overview },
  { id: "churn", label: "Churn Risk", Ic: I.churn },
  { id: "segments", label: "Segments", Ic: I.seg },
  { id: "events", label: "Event Stream", Ic: I.events },
  { id: "pipeline", label: "ML Pipeline", Ic: I.pipeline },
  { id: "health", label: "API Health", Ic: I.health },
];

// ── Resizable Sidebar ─────────────────────────────────────────────────────────
function Sidebar({ active, setActive, width, setWidth, collapsed, setCollapsed, isMobile, mobileOpen, setMobileOpen }) {
  const t = useTheme();
  const { isMobile: mob } = useResponsive();
  const dragging = useRef(false);
  const startX = useRef(0);
  const startW = useRef(0);

  // Drag to resize
  const onMouseDown = (e) => {
    dragging.current = true;
    startX.current = e.clientX;
    startW.current = width;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return;
      const delta = e.clientX - startX.current;
      const newW = Math.min(320, Math.max(180, startW.current + delta));
      setWidth(newW);
    };
    const onUp = () => {
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
  }, [setWidth]);

  const sidebarW = collapsed ? 56 : width;

  // Mobile: overlay drawer
  if (mob) {
    if (!mobileOpen) return null;
    return (
      <>
        <div onClick={() => setMobileOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 40, backdropFilter: "blur(4px)" }} />
        <div style={{ position: "fixed", left: 0, top: 0, bottom: 0, width: 220, background: t.sidebar, borderRight: `1px solid ${t.sidebarBdr}`, zIndex: 50, padding: "20px 12px", display: "flex", flexDirection: "column", overflowY: "auto" }}>
          <SidebarContent active={active} setActive={(id) => { setActive(id); setMobileOpen(false); }} collapsed={false} t={t} />
        </div>
      </>
    );
  }

  return (
    <div style={{ position: "relative", flexShrink: 0, width: sidebarW, transition: dragging.current ? "none" : "width 0.2s" }}>
      <div style={{ width: "100%", height: "100%", minHeight: "100vh", background: t.sidebar, borderRight: `1px solid ${t.sidebarBdr}`, padding: collapsed ? "20px 8px" : "20px 12px", display: "flex", flexDirection: "column", overflowY: "auto", overflowX: "hidden" }}>
        {/* Collapse toggle — top */}
        <div style={{ display: "flex", justifyContent: collapsed ? "center" : "flex-end", marginBottom: 8 }}>
          <button onClick={() => setCollapsed(c => !c)} style={{ width: 28, height: 28, borderRadius: 8, border: `1px solid ${t.border}`, background: t.surface, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: t.textMuted, flexShrink: 0 }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d={collapsed ? "M4 2l4 4-4 4" : "M8 2L4 6l4 4"} stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
        </div>
        <SidebarContent active={active} setActive={setActive} collapsed={collapsed} t={t} />
      </div>
      {/* Drag handle */}
      {!collapsed && (
        <div onMouseDown={onMouseDown} style={{ position: "absolute", top: 0, right: -3, width: 6, height: "100%", cursor: "col-resize", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "center", opacity: 0, transition: "opacity 0.2s" }}
          onMouseEnter={e => e.currentTarget.style.opacity = "1"}
          onMouseLeave={e => e.currentTarget.style.opacity = "0"}>
          <div style={{ width: 2, height: 60, borderRadius: 2, background: C.indigo, opacity: 0.6 }} />
        </div>
      )}
    </div>
  );
}

function SidebarContent({ active, setActive, collapsed, t }) {
  return (
    <>
      {/* Logo */}
      <div style={{ padding: collapsed ? "2px 4px" : "4px 10px", marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: collapsed ? 0 : 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: `linear-gradient(135deg,${C.indigo},${C.emerald})`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 11L5.5 6l2.5 3L11 3" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </div>
          {!collapsed && (
            <div>
              <p style={{ fontSize: 14, fontWeight: 700, color: t.text, letterSpacing: "-0.02em" }}>AnalytIQ</p>
              <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <GlowDot color={C.emerald} size={4} pulse />
                <p style={{ fontSize: 10, color: t.textMuted }}>v2.0 · AWS Sydney</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {!collapsed && <p style={{ fontSize: 9, fontWeight: 700, color: t.textMuted, letterSpacing: "0.1em", textTransform: "uppercase", padding: "0 10px", marginBottom: 6 }}>Workspace</p>}

      <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV.map(({ id, label, Ic }) => {
          const on = active === id;
          return (
            <button key={id} onClick={() => setActive(id)} title={collapsed ? label : ""} style={{
              display: "flex", alignItems: "center", gap: collapsed ? 0 : 9,
              padding: collapsed ? "9px 0" : "8px 10px",
              justifyContent: collapsed ? "center" : "flex-start",
              borderRadius: 10, border: "none", cursor: "pointer", textAlign: "left", transition: "all 0.15s",
              background: on ? t.navActive : "transparent",
              color: on ? t.navActiveT : t.textSub,
              fontWeight: on ? 600 : 400, fontSize: 13,
              borderLeft: on && !collapsed ? `2px solid ${C.indigo}` : "2px solid transparent",
            }}>
              <span style={{ opacity: on ? 1 : 0.55 }}><Ic /></span>
              {!collapsed && label}
              {on && !collapsed && <div style={{ marginLeft: "auto", width: 4, height: 4, borderRadius: "50%", background: t.navActiveT }} />}
            </button>
          );
        })}
      </nav>

      {!collapsed && (
        <div style={{ marginTop: "auto", paddingTop: 16 }}>
          <div style={{ padding: "11px", borderRadius: 10, background: t.statusBg, border: `1px solid ${t.statusBdr}`, marginBottom: 8 }}>
            <p style={{ fontSize: 9, fontWeight: 700, color: C.emerald, letterSpacing: "0.07em", marginBottom: 6 }}>PIPELINE STATUS</p>
            {[{ n: "Kinesis" }, { n: "Redshift" }, { n: "ML Scorer" }].map(s => (
              <div key={s.n} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                <GlowDot color={C.emerald} size={4} pulse />
                <span style={{ fontSize: 10, color: t.textMuted }}>{s.n}</span>
                <span style={{ marginLeft: "auto", fontSize: 9, color: C.emerald, fontWeight: 600 }}>live</span>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", borderRadius: 10, background: t.surface, border: `1px solid ${t.border}` }}>
            <div style={{ width: 26, height: 26, borderRadius: 7, background: `linear-gradient(135deg,${C.indigo},${C.violet})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "#fff", flexShrink: 0 }}>T</div>
            <div style={{ minWidth: 0 }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: t.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Tanvi R.</p>
              <p style={{ fontSize: 10, color: t.textMuted }}>Admin</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Overview ──────────────────────────────────────────────────────────────────
function OverviewPage({ overview, dau, segments }) {
  const t = useTheme();
  const { isMobile } = useResponsive();
  const dd = (dau || []).map(d => ({ ...d, date: d.event_date?.slice(5) }));
  const sd = (segments || []).map(s => ({ name: s.segment?.replace("_", " "), value: s.user_count, color: SEG_COLORS[s.segment] || C.slate, pct: s.pct }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr 1fr" : "repeat(4,1fr)", gap: 12 }}>
        <KPI label="Daily Active Users" value={overview?.dau} color={C.indigo} sub="unique users" delta="3.2%" deltaUp spark={dd} sparkKey="dau" />
        <KPI label="Monthly Active Users" value={overview?.mau} color={C.emerald} sub="total users" delta="8.1%" deltaUp spark={dd} sparkKey="dau" />
        <KPI label="Avg Session" value={overview?.avg_session_secs} color={C.amber} sub="seconds" suffix="s" />
        <KPI label="High Churn Risk" value={overview?.high_churn_count} color={C.rose} sub="need attention" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 290px", gap: 12 }}>
        <Card>
          <SH title="Daily Active Users" sub="8-day rolling window" right={<Badge label="LIVE" color={C.indigo} />} />
          <ResponsiveContainer width="100%" height={isMobile ? 160 : 210}>
            <AreaChart data={dd}>
              <defs>
                <linearGradient id="ag1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={C.indigo} stopOpacity={t.dark ? 0.28 : 0.15} />
                  <stop offset="100%" stopColor={C.indigo} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={t.chart} vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<Tip />} />
              <Area type="monotone" dataKey="dau" name="DAU" stroke={C.indigo} strokeWidth={2} fill="url(#ag1)" dot={false} activeDot={{ r: 4, fill: C.indigo, strokeWidth: 0 }} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        {!isMobile && (
          <Card>
            <SH title="Segments" sub={`${(segments || []).reduce((a, s) => a + s.user_count, 0)} users`} />
            <ResponsiveContainer width="100%" height={130}>
              <PieChart>
                <Pie data={sd} cx="50%" cy="50%" innerRadius={36} outerRadius={56} paddingAngle={3} dataKey="value" strokeWidth={0}>
                  {sd.map((s, i) => <Cell key={i} fill={s.color} />)}
                </Pie>
                <Tooltip content={<Tip />} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
              {sd.map(s => (
                <div key={s.name} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                  <div style={{ width: 6, height: 6, borderRadius: 2, background: s.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 11, color: t.textSub, flex: 1, textTransform: "capitalize" }}>{s.name}</span>
                  <span style={{ fontSize: 10, color: t.textMuted }}>{s.pct?.toFixed(0)}%</span>
                  <span style={{ fontSize: 11, color: t.text, fontWeight: 600 }}>{s.value}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: 12 }}>
        <Card>
          <SH title="Events per Day" sub="Total ingestion volume" />
          <ResponsiveContainer width="100%" height={isMobile ? 130 : 155}>
            <BarChart data={dd} barSize={16}>
              <CartesianGrid strokeDasharray="3 3" stroke={t.chart} vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} width={28} />
              <Tooltip content={<Tip />} />
              <Bar dataKey="total_events" name="Events" fill={C.indigo} radius={[4, 4, 0, 0]} opacity={0.85} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <SH title="Sessions per Day" sub="Unique sessions" />
          <ResponsiveContainer width="100%" height={isMobile ? 130 : 155}>
            <BarChart data={dd} barSize={16}>
              <CartesianGrid strokeDasharray="3 3" stroke={t.chart} vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} width={28} />
              <Tooltip content={<Tip />} />
              <Bar dataKey="total_sessions" name="Sessions" fill={C.emerald} radius={[4, 4, 0, 0]} opacity={0.85} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}

// ── Churn ─────────────────────────────────────────────────────────────────────
function ChurnPage({ atRisk }) {
  const t = useTheme();
  const { isMobile } = useResponsive();
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("churn_score");
  const [search, setSearch] = useState("");

  const rows = (atRisk || [])
    .filter(u => filter === "all" || u.churn_risk === filter)
    .filter(u => !search || u.company?.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => (b[sort] || 0) - (a[sort] || 0));

  const counts = { high: 0, medium: 0, low: 0 };
  (atRisk || []).forEach(u => { if (counts[u.churn_risk] !== undefined) counts[u.churn_risk]++; });

  const dist = [
    { name: "0.0–0.2", count: (atRisk || []).filter(u => (u.churn_score || 0) < 0.2).length, fill: C.emerald },
    { name: "0.2–0.4", count: (atRisk || []).filter(u => (u.churn_score || 0) >= 0.2 && (u.churn_score || 0) < 0.4).length, fill: "#3B82F6" },
    { name: "0.4–0.6", count: (atRisk || []).filter(u => (u.churn_score || 0) >= 0.4 && (u.churn_score || 0) < 0.6).length, fill: C.amber },
    { name: "0.6–0.8", count: (atRisk || []).filter(u => (u.churn_score || 0) >= 0.6 && (u.churn_score || 0) < 0.8).length, fill: "#F97316" },
    { name: "0.8–1.0", count: (atRisk || []).filter(u => (u.churn_score || 0) >= 0.8).length, fill: C.rose },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>
        {["high", "medium", "low"].map(r => {
          const cfg = RISK[r];
          return (
            <div key={r} onClick={() => setFilter(filter === r ? "all" : r)} style={{
              background: filter === r ? cfg.bg : t.surface, border: `1px solid ${filter === r ? cfg.border : t.border}`,
              borderRadius: 13, padding: "16px 18px", cursor: "pointer", transition: "all 0.15s",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}>
                <GlowDot color={cfg.text} size={6} pulse={filter === r} />
                <p style={{ fontSize: 10, color: cfg.text, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em" }}>{r} risk</p>
              </div>
              <p style={{ fontSize: isMobile ? 24 : 30, fontWeight: 700, color: t.text, letterSpacing: "-0.03em" }}>{counts[r]}</p>
              <p style={{ fontSize: 11, color: t.textMuted, marginTop: 3 }}>{((counts[r] / (atRisk?.length || 1)) * 100).toFixed(0)}% of total</p>
            </div>
          );
        })}
      </div>

      <Card>
        <SH title="Score Distribution" sub="XGBoost ML classifier output" />
        <ResponsiveContainer width="100%" height={130}>
          <BarChart data={dist} barSize={32}>
            <CartesianGrid strokeDasharray="3 3" stroke={t.chart} vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} width={24} />
            <Tooltip content={<Tip />} />
            <Bar dataKey="count" name="Users" radius={[4, 4, 0, 0]}>{dist.map((d, i) => <Cell key={i} fill={d.fill} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card style={{ padding: 0 }}>
        <div style={{ padding: "14px 18px", borderBottom: `1px solid ${t.border}`, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 120 }}>
            <p style={{ fontSize: 13, fontWeight: 600, color: t.text }}>At-Risk Customers</p>
            <p style={{ fontSize: 11, color: t.textMuted, marginTop: 1 }}>{rows.length} showing</p>
          </div>
          {!isMobile && <>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search company..."
              style={{ background: t.input, border: `1px solid ${t.inputBdr}`, borderRadius: 8, padding: "5px 11px", fontSize: 12, color: t.text, outline: "none", width: 160 }} />
            <select value={sort} onChange={e => setSort(e.target.value)}
              style={{ background: t.selectBg, border: `1px solid ${t.inputBdr}`, borderRadius: 8, padding: "5px 10px", fontSize: 12, color: t.text, outline: "none" }}>
              <option value="churn_score">Churn Score</option>
              <option value="days_inactive">Days Inactive</option>
            </select>
          </>}
          {["all", "high", "medium", "low"].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: "4px 10px", borderRadius: 20, border: `1px solid ${t.border}`, cursor: "pointer",
              background: filter === f ? `rgba(99,102,241,0.15)` : "transparent",
              color: filter === f ? C.indigo : t.textSub,
              fontSize: 11, fontWeight: filter === f ? 600 : 400, textTransform: "capitalize",
            }}>{f}</button>
          ))}
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: isMobile ? 500 : 600 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${t.border}` }}>
                {(isMobile ? ["Company", "Score", "Risk"] : ["#", "Company", "Segment", "Plan", "Days Inactive", "Score", "Risk"]).map(h => (
                  <th key={h} style={{ padding: "9px 16px", textAlign: "left", fontSize: 10, color: t.textMuted, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((u, i) => {
                const cfg = RISK[u.churn_risk] || RISK.low;
                return (
                  <tr key={u.user_id} style={{ borderBottom: `1px solid ${t.tableBdr}`, transition: "background 0.1s" }}
                    onMouseEnter={e => e.currentTarget.style.background = t.surfaceHov}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                    {!isMobile && <td style={{ padding: "10px 16px", fontSize: 11, color: t.textMuted }}>{i + 1}</td>}
                    <td style={{ padding: "10px 16px", fontSize: 13, fontWeight: 600, color: t.text, maxWidth: 160 }}>
                      <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{u.company || u.user_id?.slice(0, 14)}</span>
                    </td>
                    {!isMobile && <>
                      <td style={{ padding: "10px 16px" }}>
                        <span style={{ fontSize: 11, padding: "2px 7px", borderRadius: 6, background: `${SEG_COLORS[u.segment] || C.slate}18`, color: SEG_COLORS[u.segment] || C.slate, fontWeight: 500, textTransform: "capitalize", whiteSpace: "nowrap" }}>{u.segment?.replace("_", " ")}</span>
                      </td>
                      <td style={{ padding: "10px 16px", fontSize: 12, color: t.textSub, textTransform: "capitalize" }}>{u.plan}</td>
                      <td style={{ padding: "10px 16px" }}><span style={{ fontSize: 12, color: u.days_inactive > 5 ? C.amber : t.textSub, fontWeight: u.days_inactive > 5 ? 600 : 400 }}>{u.days_inactive}d</span></td>
                    </>}
                    <td style={{ padding: "10px 16px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: t.text, minWidth: 30 }}>{(u.churn_score || 0).toFixed(2)}</span>
                        <div style={{ width: 50, height: 4, background: t.input, borderRadius: 2, overflow: "hidden" }}>
                          <div style={{ width: `${(u.churn_score || 0) * 100}%`, height: "100%", background: cfg.text, borderRadius: 2 }} />
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: "10px 16px" }}>
                      <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 20, background: cfg.bg, color: cfg.text, fontWeight: 600, textTransform: "capitalize", border: `1px solid ${cfg.border}`, whiteSpace: "nowrap" }}>{u.churn_risk}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

// ── Segments ──────────────────────────────────────────────────────────────────
function SegmentsPage({ segments }) {
  const t = useTheme();
  const { isMobile } = useResponsive();
  const [sel, setSel] = useState(null);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr 1fr" : "repeat(auto-fill,minmax(230px,1fr))", gap: 12 }}>
        {(segments || []).map(s => {
          const c = SEG_COLORS[s.segment] || C.slate, isS = sel === s.segment;
          return (
            <div key={s.segment} onClick={() => setSel(isS ? null : s.segment)} style={{
              background: isS ? `${c}10` : t.surface, border: `1px solid ${isS ? c + "44" : t.border}`,
              borderRadius: 13, padding: "16px 18px", cursor: "pointer", transition: "all 0.2s", position: "relative", overflow: "hidden",
            }}>
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg,${c},transparent)` }} />
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <div>
                  <p style={{ fontSize: 13, fontWeight: 700, color: t.text, textTransform: "capitalize" }}>{s.segment?.replace("_", " ")}</p>
                  <p style={{ fontSize: 11, color: t.textMuted, marginTop: 2 }}>{s.user_count} users · {s.pct?.toFixed(1)}%</p>
                </div>
                <GlowDot color={c} size={8} />
              </div>
              {[{ l: "Avg Events", v: s.avg_events }, { l: "Avg Sessions", v: s.avg_sessions }].map(m => (
                <div key={m.l} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                    <span style={{ fontSize: 11, color: t.textMuted }}>{m.l}</span>
                    <span style={{ fontSize: 11, fontWeight: 600, color: t.text }}>{m.v?.toFixed(1)}</span>
                  </div>
                  <div style={{ height: 3, background: t.input, borderRadius: 2 }}>
                    <div style={{ height: "100%", width: `${Math.min(((m.v || 0) / 10) * 100, 100)}%`, background: c, borderRadius: 2 }} />
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: 12 }}>
        <Card>
          <SH title="Users by Segment" />
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={(segments || []).map(s => ({ name: s.segment?.replace("_", " "), users: s.user_count }))} barSize={22}>
              <CartesianGrid strokeDasharray="3 3" stroke={t.chart} vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} width={26} />
              <Tooltip content={<Tip />} />
              <Bar dataKey="users" name="Users" radius={[5, 5, 0, 0]}>{(segments || []).map((s, i) => <Cell key={i} fill={SEG_COLORS[s.segment] || C.slate} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <SH title="Engagement by Segment" />
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={(segments || []).map(s => ({ name: s.segment?.replace("_", " "), events: s.avg_events, sessions: s.avg_sessions }))} barSize={11} barGap={3}>
              <CartesianGrid strokeDasharray="3 3" stroke={t.chart} vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} width={26} />
              <Tooltip content={<Tip />} />
              <Bar dataKey="events" name="Avg Events" fill={C.indigo} radius={[3, 3, 0, 0]} />
              <Bar dataKey="sessions" name="Avg Sessions" fill={C.emerald} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}

// ── Events ────────────────────────────────────────────────────────────────────
function EventsPage({ dau }) {
  const t = useTheme();
  const { isMobile } = useResponsive();
  const dd = (dau || []).map(d => ({ ...d, date: d.event_date?.slice(5) }));
  const totals = { events: dd.reduce((a, d) => a + (d.total_events || 0), 0), sessions: dd.reduce((a, d) => a + (d.total_sessions || 0), 0), dau: dd.reduce((a, d) => a + (d.dau || 0), 0) };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>
        {[{ l: "Total Events", k: "total_events", v: totals.events, c: C.indigo }, { l: "Total Sessions", k: "total_sessions", v: totals.sessions, c: C.emerald }, { l: "Total DAU", k: "dau", v: totals.dau, c: C.amber }].map(m => (
          <Card key={m.l}>
            <p style={{ fontSize: 10, fontWeight: 600, color: t.textMuted, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>{m.l}</p>
            <p style={{ fontSize: 26, fontWeight: 700, color: t.text, marginBottom: 10 }}>{m.v.toLocaleString()}</p>
            <Spark data={dd} k={m.k} color={m.c} />
          </Card>
        ))}
      </div>
      <Card>
        <SH title="Event vs Session Volume" sub="Daily comparison" />
        <ResponsiveContainer width="100%" height={isMobile ? 160 : 220}>
          <LineChart data={dd}>
            <CartesianGrid strokeDasharray="3 3" stroke={t.chart} />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: t.textMuted }} axisLine={false} tickLine={false} width={30} />
            <Tooltip content={<Tip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: t.textSub }} />
            <Line type="monotone" dataKey="total_events" name="Events" stroke={C.indigo} strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
            <Line type="monotone" dataKey="total_sessions" name="Sessions" stroke={C.emerald} strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
            <Line type="monotone" dataKey="dau" name="DAU" stroke={C.amber} strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

// ── Pipeline ──────────────────────────────────────────────────────────────────
function PipelinePage() {
  const t = useTheme();
  const { isMobile } = useResponsive();
  const [pushing, setPushing] = useState(false);
  const [pushResult, setPushResult] = useState(null);

  const handlePush = async () => {
    setPushing(true); setPushResult(null);
    try {
      const r = await fetch(`${API}/ml/push-churn-to-redshift`, { method: "POST" });
      const d = await r.json();
      setPushResult({ ok: true, data: d });
    } catch (e) {
      setPushResult({ ok: false, error: e.message });
    } finally { setPushing(false); }
  };

  const steps = [
    { name: "Kinesis Data Stream", abbr: "KN", status: "live", desc: "analytiq-events · 1 shard", color: C.emerald },
    { name: "AWS Glue ETL", abbr: "GL", status: "standby", desc: "Transforms raw JSON to Redshift schema", color: C.amber },
    { name: "Amazon Redshift", abbr: "RS", status: "live", desc: "Serverless · analytiq-wg · Sydney", color: C.sky },
    { name: "K-Means Segmentation", abbr: "KM", status: "live", desc: "5 clusters · RFM features", color: C.indigo },
    { name: "XGBoost Churn Scorer", abbr: "XG", status: "live", desc: "198 users scored · AUC 0.965", color: C.violet },
    { name: "Churn Scores Push", abbr: "UP", status: "manual", desc: "Push CSV back to Redshift table", color: C.rose },
  ];

  const features = [
    { feature: "days_inactive", importance: 0.34, color: C.rose },
    { feature: "avg_events_per_day", importance: 0.22, color: C.indigo },
    { feature: "session_frequency", importance: 0.18, color: C.sky },
    { feature: "plan_type", importance: 0.12, color: C.amber },
    { feature: "total_sessions", importance: 0.09, color: C.emerald },
    { feature: "user_segment", importance: 0.05, color: C.violet },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Card>
        <SH title="ML Data Pipeline" sub="End-to-end AWS infrastructure" />
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {steps.map((s, i) => (
            <div key={s.name}>
              <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "13px 4px" }}>
                <div style={{ width: 42, height: 34, borderRadius: 9, background: `${s.color}12`, border: `1px solid ${s.color}25`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <span style={{ fontSize: 10, fontWeight: 800, color: s.color, letterSpacing: "0.05em" }}>{s.abbr}</span>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <p style={{ fontSize: 13, fontWeight: 600, color: t.text }}>{s.name}</p>
                    <span style={{ fontSize: 9, padding: "2px 7px", borderRadius: 20, background: `${s.color}14`, color: s.color, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", border: `1px solid ${s.color}25` }}>{s.status}</span>
                  </div>
                  <p style={{ fontSize: 11, color: t.textMuted, marginTop: 2 }}>{s.desc}</p>
                </div>
                {s.status === "live" && <GlowDot color={s.color} size={6} pulse />}
              </div>
              {i < steps.length - 1 && (
                <div style={{ paddingLeft: 19 }}>
                  <div style={{ width: 3, height: 18, background: `linear-gradient(${steps[i].color},${steps[i + 1].color})`, borderRadius: 2, opacity: 0.35 }} />
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: 12 }}>
        <Card style={{ border: `1px solid ${C.rose}25`, background: t.dark ? "rgba(244,63,94,0.03)" : undefined }}>
          <SH title="Push Churn Scores to Redshift" sub="Upsert churn_scores.csv into Redshift" />
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 14 }}>
            {[{ l: "Source", v: "ml/churn_scores.csv" }, { l: "Destination", v: "Redshift · public.churn_scores" }, { l: "Method", v: "Delete + insert upsert" }].map(r => (
              <div key={r.l} style={{ display: "flex", gap: 8 }}>
                <span style={{ fontSize: 11, color: t.textMuted, width: 80, flexShrink: 0 }}>{r.l}</span>
                <span style={{ fontSize: 11, color: t.text, fontWeight: 500 }}>{r.v}</span>
              </div>
            ))}
          </div>
          <button onClick={handlePush} disabled={pushing} style={{
            padding: "10px 20px", borderRadius: 10, border: `1px solid ${C.rose}35`,
            background: pushing ? "rgba(244,63,94,0.06)" : `linear-gradient(135deg,${C.rose}18,${C.violet}18)`,
            color: C.rose, fontSize: 12, fontWeight: 600, cursor: pushing ? "not-allowed" : "pointer",
            display: "flex", alignItems: "center", gap: 8, transition: "all 0.2s", width: "100%", justifyContent: "center",
          }}>
            {pushing ? "Pushing to Redshift..." : "Push Churn Scores"}
          </button>
          {pushResult && (
            <div style={{ marginTop: 12, padding: "11px 13px", borderRadius: 10, background: pushResult.ok ? "rgba(16,185,129,0.07)" : "rgba(244,63,94,0.07)", border: `1px solid ${pushResult.ok ? C.emerald : C.rose}25` }}>
              <p style={{ fontSize: 11, color: pushResult.ok ? C.emerald : C.rose, fontWeight: 700, marginBottom: 6 }}>{pushResult.ok ? "Push Successful" : "Push Failed"}</p>
              {pushResult.ok ? Object.entries(pushResult.data).map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ fontSize: 10, color: t.textMuted, textTransform: "capitalize" }}>{k.replace(/_/g, " ")}</span>
                  <span style={{ fontSize: 10, color: t.text, fontWeight: 600 }}>{String(v)}</span>
                </div>
              )) : <p style={{ fontSize: 10, color: t.textMuted }}>{pushResult.error}</p>}
            </div>
          )}
        </Card>

        <Card>
          <SH title="Feature Importance" sub="XGBoost churn predictors" />
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {features.map(f => (
              <div key={f.feature} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 11, color: t.textSub, width: 160, flexShrink: 0 }}>{f.feature}</span>
                <div style={{ flex: 1, height: 4, background: t.input, borderRadius: 2, overflow: "hidden" }}>
                  <div style={{ width: `${f.importance * 100}%`, height: "100%", background: `linear-gradient(90deg,${f.color}70,${f.color})`, borderRadius: 2, transition: "width 1s ease" }} />
                </div>
                <span style={{ fontSize: 11, color: t.text, fontWeight: 600, width: 32, textAlign: "right" }}>{(f.importance * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

// ── Health ────────────────────────────────────────────────────────────────────
function HealthPage() {
  const t = useTheme();
  const { data, error, refetch } = useFetch("/health");
  const svcs = [
    { name: "FastAPI Backend", status: "online", lat: "12ms", note: "Running on port 8000", color: C.emerald },
    { name: "Amazon Redshift", status: "online", lat: "68ms", note: "Serverless · analytiq-wg", color: C.sky },
    { name: "Amazon S3", status: "online", lat: "23ms", note: "analytiq-raw-events bucket", color: C.amber },
    { name: "Amazon Kinesis", status: "online", lat: "8ms", note: "1 shard · 24h retention", color: C.indigo },
    { name: "AWS Glue", status: "standby", lat: "—", note: "ETL jobs on demand", color: C.slate },
    { name: "ML Models", status: data?.models_loaded ? "online" : "offline", lat: "<1ms", note: "XGBoost + K-Means", color: C.violet },
  ];
  const dot = s => s === "online" ? C.emerald : s === "standby" ? C.amber : C.rose;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>
        {[{ l: "API Status", v: error ? "Degraded" : "Healthy", c: error ? C.rose : C.emerald }, { l: "Models", v: data?.models_loaded ? "Loaded" : "Missing", c: data?.models_loaded ? C.emerald : C.amber }, { l: "Region", v: "ap-southeast-2", c: C.indigo }].map(s => (
          <Card key={s.l}>
            <p style={{ fontSize: 10, fontWeight: 600, color: t.textMuted, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>{s.l}</p>
            <p style={{ fontSize: 20, fontWeight: 700, color: s.c }}>{s.v}</p>
          </Card>
        ))}
      </div>
      <Card style={{ padding: 0 }}>
        <div style={{ padding: "14px 18px", borderBottom: `1px solid ${t.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <p style={{ fontSize: 13, fontWeight: 600, color: t.text }}>Infrastructure Status</p>
            <p style={{ fontSize: 11, color: t.textMuted, marginTop: 1 }}>AWS ap-southeast-2 · Sydney</p>
          </div>
          <button onClick={refetch} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, padding: "5px 12px", borderRadius: 8, background: `rgba(99,102,241,0.1)`, border: `1px solid rgba(99,102,241,0.25)`, color: C.indigo, cursor: "pointer", fontWeight: 600 }}>
            <I.refresh /> Refresh
          </button>
        </div>
        {svcs.map((s, i) => (
          <div key={s.name} style={{ padding: "13px 18px", borderBottom: i < svcs.length - 1 ? `1px solid ${t.tableBdr}` : "none", display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 34, height: 34, borderRadius: 9, background: `${s.color}10`, border: `1px solid ${s.color}20`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <GlowDot color={dot(s.status)} size={6} pulse={s.status === "online"} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontSize: 13, fontWeight: 500, color: t.text }}>{s.name}</p>
              <p style={{ fontSize: 11, color: t.textMuted, marginTop: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.note}</p>
            </div>
            <div style={{ textAlign: "right", flexShrink: 0 }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: dot(s.status), textTransform: "capitalize" }}>{s.status}</p>
              <p style={{ fontSize: 11, color: t.textMuted, marginTop: 1 }}>{s.lat}</p>
            </div>
          </div>
        ))}
      </Card>
      {data && (
        <Card>
          <p style={{ fontSize: 10, fontWeight: 600, color: t.textMuted, letterSpacing: "0.08em", marginBottom: 10, textTransform: "uppercase" }}>Raw API Response</p>
          <pre style={{ fontSize: 11, color: C.emerald, background: t.codeBg, padding: "13px", borderRadius: 9, border: "1px solid rgba(16,185,129,0.14)", overflow: "auto", lineHeight: 1.6 }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────
function AppInner() {
  const t = useTheme();
  const { isMobile, isTablet } = useResponsive();
  const [tab, setTab] = useState("overview");
  const [sidebarW, setSidebarW] = useState(210);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const { data: overview, lastUpd, refetch: rO } = useFetch("/metrics/overview", 30000);
  const { data: dau, refetch: rD } = useFetch("/metrics/dau?days=8", 30000);
  const { data: segments, refetch: rS } = useFetch("/metrics/segments", 30000);
  const { data: atRisk, refetch: rR } = useFetch("/users/at-risk?limit=30", 30000);
  const refetchAll = () => { rO(); rD(); rS(); rR(); };

  const titles = { overview: "Dashboard Overview", churn: "Churn Risk Analysis", segments: "Customer Segments", events: "Event Stream", pipeline: "ML Pipeline", health: "API Health" };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: t.bg, fontFamily: "'Inter','SF Pro Text',-apple-system,BlinkMacSystemFont,sans-serif", color: t.text, transition: "background 0.3s" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        ::-webkit-scrollbar{width:4px;height:4px;}
        ::-webkit-scrollbar-thumb{background:${t.dark ? "rgba(99,102,241,0.3)" : "rgba(0,0,0,0.15)"};border-radius:2px;}
        body{background:${t.bg};}
        input::placeholder{color:${t.textMuted};}
        select option{background:${t.selectBg};color:${t.text};}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
        button{font-family:inherit;}
      `}</style>

      <Sidebar active={tab} setActive={setTab} width={sidebarW} setWidth={setSidebarW}
        collapsed={collapsed} setCollapsed={setCollapsed}
        isMobile={isMobile} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Header */}
        <div style={{ padding: isMobile ? "10px 14px" : "12px 24px", borderBottom: `1px solid ${t.sidebarBdr}`, display: "flex", justifyContent: "space-between", alignItems: "center", position: "sticky", top: 0, zIndex: 20, background: t.header, backdropFilter: "blur(20px)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {isMobile && (
              <button onClick={() => setMobileOpen(true)} style={{ width: 32, height: 32, borderRadius: 8, border: `1px solid ${t.border}`, background: t.surface, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: t.textSub }}>
                <I.menu />
              </button>
            )}
            <div>
              <h1 style={{ fontSize: isMobile ? 14 : 16, fontWeight: 700, color: t.text, letterSpacing: "-0.02em" }}>{titles[tab]}</h1>
              <p style={{ fontSize: 10, color: t.textMuted, marginTop: 1 }}>
                {new Date().toLocaleDateString("en-AU", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
                {!isMobile && lastUpd && <span style={{ marginLeft: 8 }}>· {lastUpd.toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>}
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {!isMobile && (
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10, color: t.textMuted, background: t.surface, border: `1px solid ${t.border}`, padding: "5px 10px", borderRadius: 20 }}>
                <div style={{ width: 5, height: 5, borderRadius: "50%", background: C.emerald, animation: "pulse 2s infinite" }} />
                Auto 30s
              </div>
            )}
            <button onClick={refetchAll} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, padding: "5px 10px", borderRadius: 20, background: t.surface, border: `1px solid ${t.border}`, color: t.textSub, cursor: "pointer", fontWeight: 500 }}>
              <I.refresh />{!isMobile && " Refresh"}
            </button>
            <button onClick={t.toggle} style={{ width: 32, height: 32, borderRadius: 8, border: `1px solid ${t.border}`, background: t.surface, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: t.textSub, transition: "all 0.2s" }}>
              {t.dark ? <I.sun /> : <I.moon />}
            </button>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: `linear-gradient(135deg,${C.indigo},${C.violet})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: "#fff" }}>T</div>
          </div>
        </div>

        {/* Mobile tab nav */}
        {isMobile && (
          <div style={{ display: "flex", gap: 0, overflowX: "auto", borderBottom: `1px solid ${t.border}`, background: t.sidebar, padding: "0 4px" }}>
            {NAV.map(({ id, label, Ic }) => (
              <button key={id} onClick={() => setTab(id)} style={{
                display: "flex", flexDirection: "column", alignItems: "center", gap: 3, padding: "10px 12px",
                border: "none", background: "transparent", cursor: "pointer", color: tab === id ? C.indigo : t.textMuted,
                fontWeight: tab === id ? 600 : 400, fontSize: 10, whiteSpace: "nowrap",
                borderBottom: tab === id ? `2px solid ${C.indigo}` : "2px solid transparent",
                flexShrink: 0,
              }}>
                <Ic />{label}
              </button>
            ))}
          </div>
        )}

        {/* Content */}
        <div style={{ padding: isMobile ? "14px 12px" : "20px 22px", flex: 1, overflowY: "auto" }}>
          {tab === "overview" && <OverviewPage overview={overview} dau={dau} segments={segments} />}
          {tab === "churn" && <ChurnPage atRisk={atRisk} />}
          {tab === "segments" && <SegmentsPage segments={segments} />}
          {tab === "events" && <EventsPage dau={dau} />}
          {tab === "pipeline" && <PipelinePage />}
          {tab === "health" && <HealthPage />}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return <ThemeProvider><AppInner /></ThemeProvider>;
}
