from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    @staticmethod
    def _validate_external_employee_code(
        db: Session,
        external_employee_code: str | None,
        current_employee_id: int | None = None,
    ) -> None:
        if not external_employee_code:
            return

        existing = (
            db.query(Employee)
            .filter(Employee.external_employee_code == external_employee_code)
            .first()
        )
        if existing and existing.id != current_employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bu external_employee_code zaten kullaniliyor: {external_employee_code}"
                ),
            )

    @staticmethod
    def create_employee(db: Session, emp_data: EmployeeCreate) -> Employee:
        """Yeni calisan olustur."""
        user = db.query(User).filter(User.id == emp_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kullanici bulunamadi (ID: {emp_data.user_id})",
            )

        existing_employee = db.query(Employee).filter(Employee.user_id == emp_data.user_id).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Bu kullanici zaten bir calisan olarak kayitli "
                    f"(Employee ID: {existing_employee.id})"
                ),
            )

        department = db.query(Department).filter(Department.id == emp_data.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Departman bulunamadi (ID: {emp_data.department_id})",
            )

        EmployeeService._validate_external_employee_code(
            db,
            emp_data.external_employee_code,
        )

        db_employee = Employee(**emp_data.dict())
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee

    @staticmethod
    def _attach_latest_surveys(employees: List[Employee]) -> List[Employee]:
        for emp in employees:
            if getattr(emp, "survey_responses", None):
                latest = sorted(emp.survey_responses, key=lambda x: x.period_date, reverse=True)[0]
                setattr(emp, "latest_ms", latest.score)
                setattr(emp, "latest_mte", getattr(latest, "mte_score", None))
                setattr(emp, "latest_ars", getattr(latest, "ars_score", None))

                ars = getattr(latest, "ars_score", None)
                if ars is not None:
                    if ars >= 0.6:
                        setattr(emp, "risk_level", "High")
                    elif ars >= 0.2:
                        setattr(emp, "risk_level", "Medium")
                    else:
                        setattr(emp, "risk_level", "Low")
                else:
                    setattr(emp, "risk_level", "Low")
            else:
                setattr(emp, "latest_ms", None)
                setattr(emp, "latest_mte", None)
                setattr(emp, "latest_ars", None)
                setattr(emp, "risk_level", "Low")
        return employees

    @staticmethod
    def get_all_employees(db: Session, skip: int = 0, limit: int = 100) -> List[Employee]:
        employees = db.query(Employee).offset(skip).limit(limit).all()
        return EmployeeService._attach_latest_surveys(employees)

    @staticmethod
    def get_employee_by_id(db: Session, emp_id: int) -> Employee:
        employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calisan bulunamadi (ID: {emp_id})",
            )
        return EmployeeService._attach_latest_surveys([employee])[0]

    @staticmethod
    def get_employees_by_department(db: Session, dept_id: int) -> List[Employee]:
        department = db.query(Department).filter(Department.id == dept_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Departman bulunamadi (ID: {dept_id})",
            )

        employees = db.query(Employee).filter(Employee.department_id == dept_id).all()
        return EmployeeService._attach_latest_surveys(employees)

    @staticmethod
    def update_employee(db: Session, emp_id: int, emp_data: EmployeeUpdate) -> Employee:
        employee = EmployeeService.get_employee_by_id(db, emp_id)

        if emp_data.department_id is not None:
            department = db.query(Department).filter(Department.id == emp_data.department_id).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Departman bulunamadi (ID: {emp_data.department_id})",
                )

        if emp_data.external_employee_code is not None:
            EmployeeService._validate_external_employee_code(
                db,
                emp_data.external_employee_code,
                current_employee_id=employee.id,
            )

        update_data = emp_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)

        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def delete_employee(db: Session, emp_id: int) -> dict:
        employee = EmployeeService.get_employee_by_id(db, emp_id)

        if employee.kpi_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bu calisana ait {len(employee.kpi_records)} KPI kaydi bulunuyor. "
                    "Once KPI kayitlarini silin."
                ),
            )

        if employee.survey_responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bu calisana ait {len(employee.survey_responses)} anket cevabi bulunuyor. "
                    "Once anket cevaplarini silin."
                ),
            )

        db.delete(employee)
        db.commit()
        return {"message": f"Calisan basariyla silindi (ID: {emp_id})"}
