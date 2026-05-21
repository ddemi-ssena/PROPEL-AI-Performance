"""
KUTUP Sales Department — 52-Haftalık Gerçekçi Dataset Üretici
Seed datadaki 30 satış çalışanı (SA-001..SA-030) için 2024 yılı verileri.
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(2024)

# ── Çalışan profilleri ────────────────────────────────────────────────────────
# (ID, Region, Role_Level, base_perf, base_motivation, base_workload)
EMPLOYEES = [
    ("SA-001", "Marmara",            "Senior",     0.93, 4.2, 63),
    ("SA-002", "Ege",                "Junior",     0.71, 3.7, 76),
    ("SA-003", "Karadeniz",          "Team Lead",  0.96, 4.5, 58),
    ("SA-004", "Marmara",            "Mid-Level",  0.83, 4.0, 69),
    ("SA-005", "Karadeniz",          "Team Lead",  0.77, 3.4, 81),
    ("SA-006", "Dogu Anadolu",       "Team Lead",  0.74, 3.2, 83),
    ("SA-007", "Ic Anadolu",         "Senior",     0.89, 4.2, 62),
    ("SA-008", "Marmara",            "Mid-Level",  0.84, 4.0, 68),
    ("SA-009", "Akdeniz",            "Mid-Level",  0.80, 3.8, 72),
    ("SA-010", "Akdeniz",            "Junior",     0.67, 3.4, 77),
    ("SA-011", "Akdeniz",            "Senior",     0.88, 4.1, 66),
    ("SA-012", "Guneydogu Anadolu",  "Team Lead",  0.85, 4.1, 64),
    ("SA-013", "Ic Anadolu",         "Team Lead",  0.81, 3.9, 72),
    ("SA-014", "Dogu Anadolu",       "Senior",     0.72, 3.3, 80),
    ("SA-015", "Dogu Anadolu",       "Junior",     0.63, 3.1, 81),
    ("SA-016", "Guneydogu Anadolu",  "Junior",     0.65, 3.2, 79),
    ("SA-017", "Guneydogu Anadolu",  "Team Lead",  0.83, 4.0, 65),
    ("SA-018", "Dogu Anadolu",       "Senior",     0.75, 3.5, 78),
    ("SA-019", "Akdeniz",            "Senior",     0.86, 4.1, 63),
    ("SA-020", "Dogu Anadolu",       "Junior",     0.60, 2.9, 84),
    ("SA-021", "Ege",                "Mid-Level",  0.82, 3.9, 70),
    ("SA-022", "Ic Anadolu",         "Team Lead",  0.79, 3.7, 74),
    ("SA-023", "Akdeniz",            "Junior",     0.63, 3.0, 83),
    ("SA-024", "Marmara",            "Senior",     0.92, 4.3, 61),
    ("SA-025", "Marmara",            "Team Lead",  0.94, 4.5, 60),
    ("SA-026", "Akdeniz",            "Team Lead",  0.84, 4.0, 65),
    ("SA-027", "Dogu Anadolu",       "Mid-Level",  0.69, 3.3, 81),
    ("SA-028", "Ege",                "Team Lead",  0.78, 3.6, 75),
    ("SA-029", "Dogu Anadolu",       "Team Lead",  0.73, 3.4, 79),
    ("SA-030", "Ic Anadolu",         "Mid-Level",  0.77, 3.7, 73),
    # SA-031: Hatice Yildirim — Satis Bolum Muduru (manager.satis@propel.com)
    ("SA-031", "Genel",              "Manager",    0.97, 4.6, 55),
]

REGION_MULT = {
    "Marmara": 1.12, "Ege": 1.06, "Karadeniz": 1.01,
    "Akdeniz": 1.03, "Ic Anadolu": 0.97,
    "Dogu Anadolu": 0.87, "Guneydogu Anadolu": 0.91,
    "Genel": 1.10,
}

ROLE_ACTIVITY   = {"Manager": 36, "Team Lead": 32, "Senior": 27, "Mid-Level": 21, "Junior": 16}
ROLE_LMDO       = {"Manager": 0.23, "Team Lead": 0.20, "Senior": 0.18, "Mid-Level": 0.14, "Junior": 0.11}
ROLE_WIN_RATE   = {"Manager": 0.54, "Team Lead": 0.49, "Senior": 0.44, "Mid-Level": 0.37, "Junior": 0.27}
ROLE_CYCLE_DAYS = {"Manager": 24, "Team Lead": 28, "Senior": 31, "Mid-Level": 40, "Junior": 52}
ROLE_SALE_VALUE = {"Manager": 19000, "Team Lead": 14500, "Senior": 12500, "Mid-Level": 8500, "Junior": 5500}
ROLE_SENIORITY  = {"Manager": 8.5, "Team Lead": 5.5, "Senior": 4.0, "Mid-Level": 2.5, "Junior": 1.0}

def seasonal(week: int) -> float:
    """Yıl içi satış mevsimselliği."""
    if week <= 8:   return 0.92   # Ocak-Şubat yavaş
    if week <= 17:  return 1.04   # Mart-Nisan canlanma
    if week <= 26:  return 1.08   # Mayıs-Haziran zirve
    if week <= 34:  return 0.95   # Temmuz-Ağustos yaz durgunluğu
    if week <= 43:  return 1.03   # Eylül-Ekim toparlanma
    return 1.10                    # Kasım-Aralık yılsonu baskısı

def clamp(v, lo, hi):
    return float(max(lo, min(hi, v)))

rows = []

for emp_id, region, role, base_perf, base_motiv, base_wl in EMPLOYEES:
    rng = np.random.default_rng(int(emp_id.split("-")[1]) * 7 + 13)
    reg_m = REGION_MULT.get(region, 1.0)

    # Yıl boyunca kişiye özgü trend (bazıları düşüyor, bazıları yükseliyor)
    trend = rng.uniform(-0.08, 0.08)
    motiv_history = []

    for week in range(1, 53):
        t = week / 52
        sea = seasonal(week)

        # ── Temel metrikler ─────────────────────────────────────────────────
        shgo = clamp(base_perf * sea * reg_m + trend * t + rng.normal(0, 0.07), 0.38, 1.65)

        total_activity = max(4, int(ROLE_ACTIVITY[role] * sea + rng.normal(0, 4)))

        lmdo = clamp(ROLE_LMDO[role] * reg_m + rng.normal(0, 0.03), 0.03, 0.48)

        win_rate = clamp(ROLE_WIN_RATE[role] + (shgo - 0.85) * 0.15 + rng.normal(0, 0.06), 0.08, 0.82)

        pipeline_n = max(2, int(total_activity * 0.45))
        won_deals  = max(0, int(pipeline_n * win_rate + rng.normal(0, 1)))
        lost_deals = max(0, int(pipeline_n * (1 - win_rate) + rng.normal(0, 1)))

        avg_cycle = clamp(ROLE_CYCLE_DAYS[role] / reg_m + rng.normal(0, 6), 5, 95)

        avg_value = max(1000, ROLE_SALE_VALUE[role] * reg_m * sea + rng.normal(0, 2500))

        pso = clamp(shgo * 0.85 + rng.normal(0, 0.14), 0.15, 2.50)
        pyo = clamp(0.12 + (1 - shgo) * 0.22 + rng.normal(0, 0.05), 0.01, 0.65)

        workload = clamp(base_wl + rng.normal(0, 7) + max(0, (1 / max(shgo, 0.4) - 1) * 8), 28, 100)

        tdo  = clamp(0.78 - (workload - 60) * 0.004 + (shgo - 0.8) * 0.10 + rng.normal(0, 0.07), 0.22, 0.99)
        csat = clamp(3.60 + (shgo - 0.80) * 0.90 + rng.normal(0, 0.22), 2.0, 5.0)
        complaint = clamp(0.07 - (csat - 3.5) * 0.025 + rng.normal(0, 0.025), 0.0, 0.40)
        crm  = clamp(0.84 - (workload - 68) * 0.003 + rng.normal(0, 0.06), 0.38, 0.99)

        peer_support = int(max(0, rng.poisson(2.0)))
        mentorship   = int(max(0, rng.poisson(0.9 if role in ("Manager", "Team Lead", "Senior") else 0.3)))

        motiv = clamp(
            base_motiv
            + rng.normal(0, 0.18)
            - (workload - 68) * 0.014
            - (1 - shgo) * 0.28
            + trend * t * 0.5,
            1.5, 5.0
        )
        motiv_history.append(motiv)

        gks = clamp(0.72 + rng.normal(0, 0.14), 0.15, 1.0)

        seniority = ROLE_SENIORITY[role] + rng.uniform(-0.5, 0.5)

        total_customers = max(5, int(total_activity * 0.65 + rng.normal(0, 3)))
        new_customers   = max(0, int(total_customers * lmdo + rng.normal(0, 1)))

        # ── Hedef değişkenler ────────────────────────────────────────────────
        # Performance_Drop_Target: bu hafta düşük VEYA son 4 haftaya göre %20 düşüş
        recent_shgo_avg = base_perf * sum(seasonal(max(1, week - i)) for i in range(1, 5)) / 4
        perf_drop = 1 if (shgo < 0.73 or shgo < recent_shgo_avg * 0.80) else 0

        # Burnout_Target: yüksek iş yükü + düşük motivasyon + zayıf takip
        burnout = 1 if (workload > 83 and motiv < 3.0 and tdo < 0.58) else 0

        # Resignation_Target: uzun süreli düşük motivasyon + CRM ihmali + hedef altı
        avg_motiv_4w = float(np.mean(motiv_history[-4:])) if len(motiv_history) >= 4 else motiv
        resignation = 1 if (avg_motiv_4w < 3.3 and crm < 0.72 and shgo < 0.80) else 0

        # High_Risk_Target: performans düşüşü + başka risk faktörü
        high_risk = 1 if (perf_drop and (burnout or resignation or (tdo < 0.52 and crm < 0.68))) else 0

        rows.append({
            "Employee_ID":               emp_id,
            "Year":                      2024,
            "Week":                      week,
            "Region":                    region,
            "Role_Level":                role,
            "Sales_Target_Achievement":  round(shgo, 4),
            "Total_Activity":            total_activity,
            "Lead_to_Win_Conversion":    round(lmdo, 4),
            "Proposal_Win_Rate":         round(win_rate, 4),
            "Won_Deal_Count":            won_deals,
            "Lost_Deal_Count":           lost_deals,
            "Average_Sales_Cycle_Days":  round(avg_cycle, 1),
            "Average_Sale_Value":        round(avg_value, 0),
            "Pipeline_Health_Ratio":     round(pso, 4),
            "Pipeline_Aging_Rate":       round(pyo, 4),
            "Sales_Workload_Index":      round(workload, 1),
            "Followup_OnTime_Rate":      round(tdo, 4),
            "Customer_Satisfaction":     round(csat, 2),
            "Complaint_Rate":            round(complaint, 4),
            "CRM_Usage_Rate":            round(crm, 4),
            "Peer_Support_Count":        peer_support,
            "Mentorship_Count":          mentorship,
            "Motivation_Score":          round(motiv, 2),
            "Development_Participation_Rate": round(gks, 4),
            "New_Customer_Count":        new_customers,
            "Total_Customer_Count":      total_customers,
            "Seniority_Years":           round(seniority, 1),
            "Performance_Drop_Target":   perf_drop,
            "Burnout_Target":            burnout,
            "Resignation_Target":        resignation,
            "High_Risk_Target":          high_risk,
        })

df = pd.DataFrame(rows)

print("=" * 55)
print(f"  Toplam satır   : {len(df)}")
print(f"  Çalışan sayısı : {df['Employee_ID'].nunique()}")
print(f"  Hafta aralığı  : {df['Week'].min()} – {df['Week'].max()}")
print()
print("  Hedef dağılımları:")
for col in ["Performance_Drop_Target", "Burnout_Target", "Resignation_Target", "High_Risk_Target"]:
    n = df[col].sum()
    pct = df[col].mean() * 100
    print(f"    {col:30s}: {n:4d} pozitif  ({pct:.1f}%)")
print("=" * 55)

out = Path("/app/KUTUP_Sales_52Week_2024.xlsx")
df.to_excel(out, index=False)
print(f"\n  Dosya kaydedildi: {out}")
