from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.analytics.kpi_registry import (
    KPIDefinition,
    SOFTWARE_KPI_REGISTRY,
    get_software_kpi_definition,
)
from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.kpi import KPI, KPIRecord


class SoftwareKPIImportService:
    @staticmethod
    def _resolve_department(db: Session) -> Department:
        department = db.query(Department).filter(Department.name == "Yazilim").first()
        if not department:
            raise ValueError("Yazilim departmani bulunamadi. Once seed verisini yukleyin.")
        return department

    @staticmethod
    def _resolve_kpi_map(db: Session, department_id: int) -> dict[str, KPI]:
        kpis = db.query(KPI).filter(
            or_(KPI.department_id == department_id, KPI.department_id.is_(None))
        ).all()
        mapping: dict[str, KPI] = {}
        for kpi in kpis:
            key = (kpi.description or "").split("|", 1)[0].strip()
            if key:
                mapping[key] = kpi
                definition = get_software_kpi_definition(key)
                if definition:
                    for code in definition.all_codes:
                        mapping[code] = kpi
        return mapping

    @staticmethod
    def _resolve_employee_map(db: Session, department_id: int) -> dict[str, Employee]:
        employees = db.query(Employee).filter(Employee.department_id == department_id).all()
        return {
            employee.external_employee_code: employee
            for employee in employees
            if employee.external_employee_code
        }

    @staticmethod
    def _period_date(year: int, week: int) -> date:
        return date.fromisocalendar(year, week, 1)

    @staticmethod
    def _normalize_metric_value(column_name: str, raw_value: Any, definition: KPIDefinition) -> float:
        value = float(raw_value)
        if column_name in {
            "task_completion_rate",
            "on_time_delivery_rate",
            "commit_score",
            "bug_density",
            "critical_bug_ratio",
            "code_review_acceptance",
            "workload_index",
            "org_centrality_score",
            "project_complexity",
            "management_quality",
            "attrition_risk_score",
        }:
            return round(value * 100, 2)

        if definition.unit == "ratio" and 0 <= value <= 1.5:
            return round(value * 100, 2)

        return round(value, 2)

    @staticmethod
    def import_rows(db: Session, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
        department = SoftwareKPIImportService._resolve_department(db)
        kpi_map = SoftwareKPIImportService._resolve_kpi_map(db, department.id)
        employee_map = SoftwareKPIImportService._resolve_employee_map(db, department.id)

        normalized_records: list[KPIRecord] = []
        employee_codes: set[str] = set()
        period_dates: set[date] = set()
        metric_codes_seen: set[str] = set()

        for row in rows:
            employee_id_raw = row.get("employee_id")
            week_raw = row.get("week")
            year_raw = row.get("year")
            if employee_id_raw in (None, "") or week_raw in (None, "") or year_raw in (None, ""):
                continue

            external_code = f"SE-{int(employee_id_raw):03d}"
            employee = employee_map.get(external_code)
            if not employee:
                continue

            period_date = SoftwareKPIImportService._period_date(int(year_raw), int(week_raw))
            employee_codes.add(external_code)
            period_dates.add(period_date)

            for definition in SOFTWARE_KPI_REGISTRY:
                source_column = next(
                    (
                        column_name
                        for column_name in definition.source_columns
                        if column_name in row and row[column_name] not in (None, "")
                    ),
                    None,
                )
                if not source_column:
                    continue
                kpi = kpi_map.get(definition.canonical_code)
                if not kpi:
                    continue
                metric_codes_seen.add(definition.canonical_code)
                normalized_records.append(
                    KPIRecord(
                        kpi_id=kpi.id,
                        employee_id=employee.id,
                        value=SoftwareKPIImportService._normalize_metric_value(
                            source_column,
                            row[source_column],
                            definition,
                        ),
                        period_date=period_date,
                    )
                )

        if not normalized_records:
            raise ValueError("Dosyada islenebilir KPI satiri bulunamadi.")

        imported_employee_ids = {
            employee_map[code].id
            for code in employee_codes
            if code in employee_map
        }
        imported_kpi_ids = {
            kpi_map[code].id
            for code in metric_codes_seen
            if code in kpi_map
        }

        (
            db.query(KPIRecord)
            .filter(
                KPIRecord.employee_id.in_(imported_employee_ids),
                KPIRecord.kpi_id.in_(imported_kpi_ids),
                KPIRecord.period_date.in_(period_dates),
            )
            .delete(synchronize_session=False)
        )

        db.add_all(normalized_records)
        db.commit()

        return {
            "record_count": len(normalized_records),
            "employee_count": len(imported_employee_ids),
            "period_count": len(period_dates),
            "metric_count": len(metric_codes_seen),
            "department": "software",
        }
