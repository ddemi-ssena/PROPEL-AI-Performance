"""
Satış dataseti v4 — bireysel farklılaşma + karışık risk profilleri
31 çalışan × 52 hafta = 1612 satır

Her çalışanın 4 hedef için ayrı risk oranı var (0.0–1.0).
Bu sayede model sadece "tier" değil, gerçek KPI kombinasyonlarını öğrenir.
"""
import random
from pathlib import Path

random.seed(42)

try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

YEAR = 2024

# ── Çalışan profili ───────────────────────────────────────────────────────────
# shgo: satış hedef, motiv: motivasyon, workload: iş yükü (1.0 = normal)
# crm: CRM kullanım, collab: ekip katkısı, pipeline: pipeline sağlığı
# conv: dönüşüm oranı
# risk_pd / risk_bk / risk_rs / risk_hr: haftalık olayda bu hedefin 1 olma OLASILĞI
# (stokastik — model nüanslı öğrenir)

EMPLOYEES = [
    # code         region                  role        shgo  motiv wl    crm   coll  pipe  conv  pd    bk    rs    hr
    ("SA-001", "Marmara",           "Senior",    1.15, 0.88, 0.85, 1.05, 1.0,  1.2,  1.2,  0.05, 0.12, 0.04, 0.06),
    ("SA-002", "Ege",               "Mid-Level", 1.05, 0.85, 0.88, 1.10, 1.1,  1.0,  1.0,  0.07, 0.15, 0.06, 0.08),
    ("SA-003", "Karadeniz",         "Senior",    1.20, 0.82, 0.92, 0.95, 0.9,  1.3,  1.1,  0.04, 0.20, 0.05, 0.05),  # yüksek iş yükü riski
    ("SA-004", "Marmara",           "Senior",    1.10, 0.90, 0.88, 1.0,  0.95, 1.1,  1.0,  0.06, 0.10, 0.05, 0.07),
    ("SA-005", "Karadeniz",         "Manager",   0.88, 0.72, 1.15, 0.90, 0.95, 0.90, 0.85, 0.35, 0.55, 0.28, 0.40),  # orta-yüksek burnout
    ("SA-006", "Doğu Anadolu",      "Manager",   0.85, 0.68, 1.10, 0.85, 0.80, 0.85, 0.88, 0.38, 0.50, 0.32, 0.42),
    ("SA-007", "İç Anadolu",        "Senior",    1.08, 0.92, 0.92, 1.0,  1.2,  1.0,  0.9,  0.05, 0.08, 0.04, 0.05),
    ("SA-008", "Marmara",           "Mid-Level", 0.92, 0.78, 1.05, 0.92, 0.85, 0.88, 0.80, 0.30, 0.40, 0.22, 0.32),
    ("SA-009", "Akdeniz",           "Mid-Level", 1.00, 0.87, 0.88, 1.05, 1.0,  1.0,  1.1,  0.08, 0.14, 0.07, 0.09),
    ("SA-010", "Akdeniz",           "Junior",    0.62, 0.48, 1.35, 0.65, 0.60, 0.60, 0.60, 0.82, 0.75, 0.70, 0.80),  # yüksek risk
    ("SA-011", "Akdeniz",           "Senior",    1.12, 0.85, 0.85, 0.98, 0.9,  1.1,  1.05, 0.06, 0.12, 0.05, 0.07),
    ("SA-012", "Güneydoğu Anadolu", "Team Lead", 1.05, 0.88, 0.90, 1.1,  1.3,  1.0,  0.95, 0.07, 0.10, 0.06, 0.08),
    ("SA-013", "İç Anadolu",        "Manager",   0.88, 0.70, 1.20, 0.80, 0.90, 0.92, 0.88, 0.40, 0.58, 0.30, 0.45),
    ("SA-014", "Doğu Anadolu",      "Senior",    0.70, 0.42, 1.40, 0.78, 0.75, 0.70, 0.65, 0.72, 0.80, 0.68, 0.75),  # motivasyon krizi
    ("SA-015", "Doğu Anadolu",      "Junior",    0.55, 0.50, 1.30, 0.60, 0.55, 0.55, 0.55, 0.85, 0.70, 0.72, 0.82),
    ("SA-016", "Güneydoğu Anadolu", "Junior",    0.65, 0.52, 1.28, 0.70, 0.62, 0.62, 0.62, 0.78, 0.65, 0.65, 0.75),
    ("SA-017", "Güneydoğu Anadolu", "Team Lead", 0.95, 0.78, 1.05, 0.95, 1.0,  0.90, 0.92, 0.22, 0.38, 0.18, 0.25),
    ("SA-018", "Doğu Anadolu",      "Senior",    0.80, 0.65, 1.25, 0.88, 0.85, 0.80, 0.85, 0.52, 0.65, 0.45, 0.55),
    ("SA-019", "Akdeniz",           "Senior",    1.15, 0.90, 0.90, 1.0,  1.1,  1.15, 1.1,  0.04, 0.10, 0.04, 0.05),
    ("SA-020", "Doğu Anadolu",      "Junior",    0.58, 0.45, 1.38, 0.62, 0.58, 0.58, 0.58, 0.88, 0.78, 0.75, 0.85),
    ("SA-021", "Ege",               "Mid-Level", 0.88, 0.72, 1.00, 0.90, 0.88, 0.88, 0.80, 0.28, 0.35, 0.22, 0.30),
    ("SA-022", "İç Anadolu",        "Manager",   0.92, 0.70, 1.10, 0.88, 0.92, 0.90, 0.90, 0.32, 0.45, 0.28, 0.35),
    ("SA-023", "Akdeniz",           "Junior",    0.68, 0.55, 1.20, 0.68, 0.65, 0.65, 0.65, 0.62, 0.55, 0.50, 0.60),
    ("SA-024", "Marmara",           "Senior",    1.08, 0.82, 0.95, 1.0,  1.0,  1.05, 1.0,  0.10, 0.18, 0.08, 0.12),
    ("SA-025", "Marmara",           "Manager",   0.85, 0.75, 1.05, 0.82, 0.80, 0.85, 0.88, 0.30, 0.42, 0.25, 0.32),
    ("SA-026", "Akdeniz",           "Team Lead", 1.18, 0.88, 0.90, 1.1,  1.2,  1.2,  1.15, 0.05, 0.12, 0.04, 0.06),
    ("SA-027", "Doğu Anadolu",      "Mid-Level", 0.72, 0.50, 1.32, 0.75, 0.72, 0.72, 0.70, 0.65, 0.60, 0.55, 0.65),
    ("SA-028", "Ege",               "Manager",   0.90, 0.68, 1.15, 0.88, 0.90, 0.88, 0.85, 0.35, 0.48, 0.30, 0.38),
    ("SA-029", "Doğu Anadolu",      "Team Lead", 0.82, 0.70, 1.10, 0.85, 0.95, 0.82, 0.88, 0.40, 0.45, 0.35, 0.42),
    ("SA-030", "İç Anadolu",        "Mid-Level", 0.88, 0.72, 1.08, 0.90, 0.85, 0.88, 0.82, 0.25, 0.38, 0.20, 0.28),
    ("SA-031", "Genel",             "Manager",   0.95, 0.80, 0.95, 1.0,  1.0,  0.95, 0.92, 0.10, 0.20, 0.08, 0.12),  # Yönetici
]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def r(v, d=4):
    return round(v, d)


def generate_row(code, region, role, profile, week):
    shgo_b, motiv_b, wl_b, crm_b, coll_b, pipe_b, conv_b, p_pd, p_bk, p_rs, p_hr = profile

    # Haftalık trend: kötü çalışanlar zamanla daha kötüleşir
    trend = (week - 26) / 52
    motiv_val  = clamp(r(4.0*motiv_b + trend*(-0.4 if motiv_b < 0.65 else 0.05) + random.gauss(0, 0.25)), 1.0, 5.0)
    shgo_val   = clamp(r(shgo_b + trend*(-0.02 if shgo_b < 0.75 else 0.01) + random.gauss(0, 0.07)), 0.25, 1.65)
    workload   = clamp(r(wl_b + trend*(0.05 if wl_b > 1.1 else -0.02) + random.gauss(0, 0.08)), 0.4, 2.2)
    conv_val   = clamp(r(conv_b + random.gauss(0, 0.06)), 0.20, 1.40)
    crm_val    = clamp(r(crm_b + random.gauss(0, 0.04)), 0.20, 1.0)
    follow_val = clamp(r(min(crm_b, conv_b) + random.gauss(0, 0.04)), 0.20, 1.0)
    csat_val   = clamp(r(4.5*min(conv_b, 1.1) + random.gauss(0, 0.20)), 1.0, 5.0)
    pipe_val   = clamp(r(3.0*pipe_b + random.gauss(0, 0.25)), 0.3, 8.0)
    aged_val   = clamp(r((1-pipe_b)*0.4 + random.gauss(0, 0.04)), 0.0, 0.85)
    complaint  = clamp(r((1-min(conv_b,1.0))*0.15 + random.gauss(0, 0.02)), 0.0, 0.50)
    act_raw    = max(5, round(30*conv_b + random.gauss(0, 3)))
    nmko_val   = clamp(r(0.30*conv_b + random.gauss(0, 0.03)), 0.01, 0.65)
    lmdo_val   = clamp(r(0.25*conv_b + random.gauss(0, 0.03)), 0.01, 0.55)
    tko_val    = clamp(r(0.50*conv_b + random.gauss(0, 0.05)), 0.05, 0.90)
    osds       = clamp(r(30/max(shgo_val,0.4) + random.gauss(0, 5)), 10, 120)
    avg_sale   = clamp(r(15000*shgo_val + random.gauss(0, 1200)), 2000, 35000)
    won        = max(0, round(5*shgo_val + random.gauss(0, 1.0)))
    lost       = max(0, round(3/max(shgo_val,0.4) + random.gauss(0, 0.8)))
    peer       = max(0, round(3*coll_b + random.gauss(0, 0.5)))
    mentor     = max(0, round(2*coll_b + random.gauss(0, 0.4)))
    team_c     = clamp(r(5*coll_b + random.gauss(0, 0.4)), 0.0, 12.0)
    dev_part   = clamp(r(0.85 + (coll_b-0.7)*0.5 + random.gauss(0, 0.07)), 0.0, 1.5)

    weekly_target  = 50000
    weekly_revenue = clamp(r(weekly_target * shgo_val), 5000, 120000)

    # Stokastik risk etiketleri — her haftada bağımsız Bernoulli çekimi
    # Burada ek KPI sinyal gürültüsü eklenip olasılık biraz kaydırılıyor
    def label(base_p, kpi_nudge=0.0):
        p = clamp(base_p + kpi_nudge + random.gauss(0, 0.08), 0.01, 0.99)
        return 1 if random.random() < p else 0

    motiv_nudge   = (motiv_b - motiv_val/4.0) * 0.15
    workload_nudge= (workload - 1.0) * 0.12
    shgo_nudge    = (1 - shgo_val) * 0.10

    perf_drop   = label(p_pd, shgo_nudge + motiv_nudge)
    burnout     = label(p_bk, workload_nudge + motiv_nudge)
    resignation = label(p_rs, motiv_nudge + shgo_nudge)
    high_risk   = label(p_hr, (shgo_nudge + motiv_nudge + workload_nudge) * 0.5)

    return {
        "Employee_ID":                    code,
        "Year":                           YEAR,
        "Week":                           week,
        "Region":                         region,
        "Role_Level":                     role,
        "Weekly_Sales_Revenue":           weekly_revenue,
        "Weekly_Sales_Target":            weekly_target,
        "Sales_Target_Achievement":       shgo_val,
        "Total_Activity":                 act_raw,
        "New_Customer_Acquisition_Rate":  nmko_val,
        "Lead_to_Win_Conversion":         lmdo_val,
        "Proposal_Win_Rate":              tko_val,
        "Won_Deal_Count":                 won,
        "Lost_Deal_Count":                lost,
        "Average_Sales_Cycle_Days":       osds,
        "Average_Sale_Value":             avg_sale,
        "Pipeline_Health_Ratio":          pipe_val,
        "Pipeline_Aging_Rate":            aged_val,
        "Sales_Workload_Index":           workload,
        "Followup_OnTime_Rate":           follow_val,
        "Customer_Satisfaction":          csat_val,
        "Complaint_Rate":                 complaint,
        "CRM_Usage_Rate":                 crm_val,
        "Peer_Support_Count":             peer,
        "Mentorship_Count":               mentor,
        "Team_Contribution_Score":        team_c,
        "Motivation_Score":               motiv_val,
        "Development_Participation_Rate": dev_part,
        "Performance_Drop_Target":        perf_drop,
        "Burnout_Target":                 burnout,
        "Resignation_Target":             resignation,
        "High_Risk_Target":               high_risk,
    }


def main():
    out = Path(__file__).parent / "sales_dataset_v3.xlsx"
    rows = []
    for emp in EMPLOYEES:
        code, region, role = emp[0], emp[1], emp[2]
        profile = emp[3:]
        for week in range(1, 53):
            rows.append(generate_row(code, region, role, profile, week))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales_Data"
    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([row[h] for h in headers])
    wb.save(out)
    print(f"Yazildi: {out}  ({len(rows)} satir)")

    from collections import Counter
    for col in ("Performance_Drop_Target", "Burnout_Target", "Resignation_Target", "High_Risk_Target"):
        dist = Counter(r[col] for r in rows)
        pct1 = dist[1] / len(rows) * 100
        print(f"  {col}: 0={dist[0]}, 1={dist[1]} ({pct1:.1f}%)")

    print("\nÇalışan bazlı ortalama risk (tüm):")
    for emp in EMPLOYEES:
        code = emp[0]
        emp_rows = [r for r in rows if r["Employee_ID"] == code]
        pd_r = sum(r["Performance_Drop_Target"] for r in emp_rows) / len(emp_rows)
        bk_r = sum(r["Burnout_Target"] for r in emp_rows) / len(emp_rows)
        rs_r = sum(r["Resignation_Target"] for r in emp_rows) / len(emp_rows)
        hr_r = sum(r["High_Risk_Target"] for r in emp_rows) / len(emp_rows)
        print(f"  {code}: PD={pd_r:.0%} BK={bk_r:.0%} RS={rs_r:.0%} HR={hr_r:.0%}")


if __name__ == "__main__":
    main()
