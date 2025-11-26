from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from ..base_class import BaseModel

class UserRole(str, enum.Enum):
    admin = "admin"
    department_manager = "department_manager"
    employee = "employee"

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.employee, nullable=False)
    is_active = Column(Boolean, default=True)  # ✅ Boolean'a çevrildi
    
    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False)