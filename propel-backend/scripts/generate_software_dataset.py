"""
Yazılım departmanı dataseti v2 — 4 hedef + bireysel profil
31 çalışan × 52 hafta = 1612 satır (MGR-SW dahil)

Her çalışanın bireysel KPI profili: farklı güçlü/zayıf yönler
4 stokastik hedef: Performance_Drop_Target, Burnout_Target,
                   Resignation_Target, High_Risk_Target
"""
import csv, random
from pathlib import Path

random.seed(13)
YEAR = 2024

# (code, team, role, exp,  gto,  zto,  gke,  kkke, by,   crko, wl,   ms,   fb,   pd,   bk,   rs,   hr)
# gto=task_completion, zto=on_time, gke=commit_score, kkke=code_quality
# by=bug_density(lower better), crko=code_review, wl=workload, ms=motivation, fb=feedback
# pd/bk/rs/hr = risk olasılıkları (0.0-1.0)
EMPLOYEES = [
    # Yüksek performanslı
    ("SE-001","Backend",  "Senior",  6, 0.92,0.88,1.20,0.80,0.22,0.88,0.85,0.88,0.82, 0.05,0.10,0.04,0.06),
    ("SE-002","Frontend", "Mid-Level",4, 0.88,0.85,1.05,0.78,0.28,0.85,0.88,0.85,0.80, 0.07,0.14,0.06,0.08),
    ("SE-003","Backend",  "Senior",  8, 0.94,0.90,1.25,0.85,0.18,0.92,0.90,0.90,0.88, 0.04,0.12,0.03,0.05),
    ("SE-004","DevOps",   "Senior",  7, 0.90,0.88,1.15,0.82,0.20,0.88,0.88,0.88,0.85, 0.06,0.10,0.05,0.07),
    ("SE-005","Frontend", "Senior",  5, 0.88,0.85,1.10,0.80,0.25,0.85,0.85,0.85,0.82, 0.07,0.12,0.06,0.08),
    ("SE-006","Backend",  "Lead",    9, 0.95,0.92,1.30,0.88,0.15,0.94,0.92,0.92,0.90, 0.03,0.18,0.03,0.04),  # yüksek iş yükü riski
    ("SE-007","Frontend", "Mid-Level",4, 0.86,0.83,1.08,0.76,0.30,0.83,0.88,0.83,0.80, 0.08,0.15,0.07,0.09),
    ("SE-008","Backend",  "Senior",  6, 0.90,0.88,1.18,0.82,0.22,0.88,0.88,0.88,0.85, 0.06,0.12,0.05,0.07),
    ("SE-009","DevOps",   "Mid-Level",3, 0.85,0.82,1.02,0.75,0.32,0.82,0.88,0.82,0.78, 0.10,0.15,0.08,0.10),
    ("SE-010","Frontend", "Senior",  7, 0.92,0.88,1.20,0.84,0.20,0.90,0.90,0.90,0.88, 0.05,0.10,0.04,0.06),
    ("SE-011","Backend",  "Lead",   10, 0.96,0.93,1.35,0.90,0.12,0.95,0.92,0.92,0.90, 0.03,0.20,0.03,0.04),  # burnout riski yüksek (yoğun çalışıyor)
    # Orta performanslı
    ("SE-012","Frontend", "Junior",  2, 0.72,0.68,0.88,0.65,0.45,0.70,0.95,0.70,0.65, 0.28,0.40,0.22,0.30),
    ("SE-013","Backend",  "Mid-Level",4, 0.78,0.75,0.95,0.70,0.38,0.75,0.90,0.75,0.72, 0.22,0.38,0.18,0.25),
    ("SE-014","DevOps",   "Mid-Level",3, 0.75,0.72,0.90,0.68,0.42,0.72,0.92,0.72,0.70, 0.25,0.42,0.20,0.28),
    ("SE-015","Backend",  "Junior",  2, 0.70,0.65,0.85,0.62,0.48,0.68,0.98,0.68,0.65, 0.30,0.48,0.25,0.32),  # iş yükü stresi
    ("SE-016","Frontend", "Mid-Level",3, 0.76,0.73,0.92,0.70,0.40,0.73,0.88,0.73,0.70, 0.22,0.35,0.18,0.24),
    ("SE-017","Backend",  "Mid-Level",4, 0.80,0.76,0.98,0.72,0.36,0.76,0.88,0.76,0.74, 0.18,0.32,0.15,0.20),
    ("SE-018","DevOps",   "Junior",  1, 0.68,0.62,0.82,0.60,0.52,0.65,0.95,0.65,0.62, 0.35,0.50,0.28,0.38),
    ("SE-019","Frontend", "Mid-Level",3, 0.78,0.75,0.94,0.70,0.38,0.75,0.88,0.75,0.72, 0.22,0.35,0.18,0.24),
    ("SE-020","Backend",  "Junior",  2, 0.72,0.68,0.86,0.65,0.45,0.68,0.92,0.68,0.65, 0.28,0.42,0.22,0.30),
    ("SE-021","BackendX", "Junior",  1, 0.65,0.60,0.80,0.58,0.55,0.62,0.96,0.62,0.60, 0.35,0.52,0.28,0.38),
    ("SE-022","FrontendX","Junior",  2, 0.70,0.65,0.85,0.62,0.48,0.66,0.94,0.66,0.63, 0.30,0.45,0.24,0.32),
    # Düşük performanslı
    ("SE-023","Backend",  "Junior",  2, 0.55,0.50,0.68,0.48,0.68,0.52,1.35,0.48,0.45, 0.80,0.72,0.68,0.78),
    ("SE-024","Frontend", "Junior",  1, 0.50,0.45,0.62,0.44,0.75,0.48,1.40,0.42,0.40, 0.85,0.75,0.72,0.82),
    ("SE-025","Backend",  "Mid-Level",3, 0.60,0.55,0.75,0.52,0.62,0.56,1.30,0.52,0.50, 0.72,0.65,0.60,0.70),
    ("SE-026","DevOps",   "Junior",  2, 0.55,0.50,0.70,0.48,0.68,0.52,1.38,0.48,0.45, 0.78,0.70,0.65,0.75),
    ("SE-027","Frontend", "Junior",  1, 0.48,0.42,0.60,0.42,0.78,0.45,1.42,0.40,0.38, 0.88,0.78,0.75,0.85),
    ("SE-028","Backend",  "Junior",  2, 0.58,0.52,0.72,0.50,0.65,0.54,1.32,0.50,0.48, 0.75,0.68,0.62,0.72),
    ("SE-029","Frontend", "Junior",  1, 0.52,0.48,0.65,0.46,0.72,0.50,1.36,0.46,0.44, 0.82,0.72,0.70,0.80),
    ("SE-030","DevOps",   "Junior",  2, 0.55,0.50,0.68,0.48,0.68,0.52,1.35,0.48,0.46, 0.78,0.70,0.65,0.75),
    ("MGR-SW","Genel",    "Manager",12, 0.88,0.85,1.10,0.82,0.25,0.85,0.92,0.88,0.85, 0.08,0.20,0.06,0.10),
]


def clamp(v, lo, hi): return max(lo, min(hi, v))
def r(v, d=4): return round(v, d)


def generate_row(code, team, role, exp, profile, week):
    gto_b,zto_b,gke_b,kkke_b,by_b,crko_b,wl_b,ms_b,fb_b, p_pd,p_bk,p_rs,p_hr = profile

    trend = (week - 26) / 52
    ms_nudge = trend * (-0.3 if ms_b < 0.65 else 0.05)
    wl_nudge  = trend * (0.06 if wl_b > 1.1 else -0.02)

    gto  = clamp(r(gto_b  + random.gauss(0, 0.04)), 0.25, 1.0)
    zto  = clamp(r(zto_b  + random.gauss(0, 0.04)), 0.20, 1.0)
    gke  = clamp(r(gke_b  + random.gauss(0, 0.06)), 0.20, 1.80)
    kkke = clamp(r(kkke_b + random.gauss(0, 0.04)), 0.15, 1.0)
    by_  = clamp(r(by_b   + random.gauss(0, 0.05)), 0.0,  2.0)
    kbo  = clamp(r(by_b * 0.6 + random.gauss(0, 0.03)), 0.0, 1.0)
    crko = clamp(r(crko_b + random.gauss(0, 0.04)), 0.20, 1.0)
    opds = clamp(r(1.5 / max(crko_b, 0.4) + random.gauss(0, 0.2)), 0.5, 6.0)
    wl   = clamp(r(wl_b + wl_nudge + random.gauss(0, 0.08)), 0.4, 2.2)
    tyo  = clamp(r(wl * 0.15 + random.gauss(0, 0.03)), 0.05, 0.7)
    ms   = clamp(r(ms_b * 10 + ms_nudge + random.gauss(0, 0.4)), 1.0, 10.0)
    fb   = clamp(r(fb_b + random.gauss(0, 0.04)), 0.20, 1.0)
    oms  = clamp(r(fb_b * 0.9 + random.gauss(0, 0.04)), 0.10, 1.0)

    assigned  = random.randint(6, 14)
    completed = max(1, round(assigned * gto))
    sp = random.randint(10, 40)
    hours = clamp(round(40 + (wl - 1.0) * 20 + random.gauss(0, 3)), 20, 65)

    def label(base_p, nudge=0.0):
        p = clamp(base_p + nudge + random.gauss(0, 0.07), 0.01, 0.99)
        return 1 if random.random() < p else 0

    perf_nudge = (gto_b - gto) * 0.2 + (kkke_b - kkke) * 0.15
    burn_nudge = (wl - 1.0) * 0.15 + (8.0 - ms) / 10.0 * 0.10
    res_nudge  = (8.0 - ms) / 10.0 * 0.15 + (gto_b - gto) * 0.10

    perf_drop   = label(p_pd, perf_nudge)
    burnout     = label(p_bk, burn_nudge)
    resignation = label(p_rs, res_nudge)
    high_risk   = label(p_hr, (perf_nudge + burn_nudge + res_nudge) * 0.4)

    return {
        "employee_id":              code,
        "year":                     YEAR,
        "week":                     week,
        "team":                     team,
        "role":                     role,
        "experience_years":         exp,
        "assigned_tasks":           assigned,
        "completed_tasks":          completed,
        "story_points_completed":   sp,
        "actual_work_hours":        hours,
        "task_completion_rate":     gto,
        "on_time_delivery_rate":    zto,
        "commit_score":             gke,
        "project_complexity":       kkke,
        "bug_density":              by_,
        "critical_bug_ratio":       kbo,
        "code_review_acceptance":   crko,
        "avg_pr_revision":          opds,
        "workload_index":           wl,
        "team_collaboration_score": tyo,
        "feedback_score":           fb,
        "org_centrality_score":     oms,
        "motivation_score":         r(ms / 10.0, 4),  # 0-1 normalize
        "Performance_Drop_Target":  perf_drop,
        "Burnout_Target":           burnout,
        "Resignation_Target":       resignation,
        "High_Risk_Target":         high_risk,
    }


def main():
    out = Path(__file__).parent / "software_dataset_v2.csv"
    rows = []
    for emp in EMPLOYEES:
        code, team, role, exp = emp[0], emp[1], emp[2], emp[3]
        profile = emp[4:]
        for week in range(1, 53):
            rows.append(generate_row(code, team, role, exp, profile, week))

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Yazildi: {out}  ({len(rows)} satir)")

    from collections import Counter
    for col in ("Performance_Drop_Target","Burnout_Target","Resignation_Target","High_Risk_Target"):
        d = Counter(r[col] for r in rows)
        print(f"  {col}: 0={d[0]}, 1={d[1]} ({d[1]/len(rows)*100:.1f}%)")

    print("\nÇalışan bazlı (ilk 10):")
    for emp in EMPLOYEES[:10]:
        code = emp[0]
        er = [r for r in rows if r["employee_id"] == code]
        pd_r = sum(r["Performance_Drop_Target"] for r in er) / len(er)
        bk_r = sum(r["Burnout_Target"] for r in er) / len(er)
        rs_r = sum(r["Resignation_Target"] for r in er) / len(er)
        print(f"  {code}: PD={pd_r:.0%} BK={bk_r:.0%} RS={rs_r:.0%}")


if __name__ == "__main__":
    main()
