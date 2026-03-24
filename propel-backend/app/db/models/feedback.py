# propel-backend/app/db/models/feedback.py
# 360° Geri Bildirim Modülü — Veritabanı Modelleri

from sqlalchemy import Column, String, Text, Float, Integer, Date, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum
from ..base_class import BaseModel


# ──────────────────────────────────────────────
# ENUM'lar
# ──────────────────────────────────────────────

class FeedbackType(str, enum.Enum):
    """Geri bildirimin yönü — kim kime veriyor"""
    manager_to_employee = "manager_to_employee"   # Yöneticiden çalışana
    employee_to_manager = "employee_to_manager"   # Çalışandan yöneticiye (yukarı)
    peer_to_peer        = "peer_to_peer"           # Eşten eşe (yatay)
    self_assessment     = "self_assessment"        # Kendi kendine değerlendirme


class FeedbackStatus(str, enum.Enum):
    """Geri bildirim talebi durumu"""
    pending   = "pending"    # Bekliyor
    completed = "completed"  # Tamamlandı
    declined  = "declined"   # Reddedildi
    expired   = "expired"    # Süresi doldu


class BadgeType(str, enum.Enum):
    """Rozet türleri — NLP analizi sonucu kazanılır"""
    team_player      = "team_player"       # 🤝 Takım Kaptanı
    problem_solver   = "problem_solver"    # 💡 Problem Avcısı
    communicator     = "communicator"      # 🗣️ Kristal Konuşmacı
    speed_champion   = "speed_champion"    # ⚡ Hız Şampiyonu
    mentor           = "mentor"            # 🎓 Bilgi Aktarıcı
    innovator        = "innovator"         # 🚀 Yenilikçi
    reliable         = "reliable"          # 🔒 Güvenilir


class BadgeLevel(str, enum.Enum):
    """Rozet seviyeleri"""
    bronze = "bronze"
    silver = "silver"
    gold   = "gold"


# ──────────────────────────────────────────────
# MODEL 1: Feedback (Geri Bildirim)
# ──────────────────────────────────────────────

class Feedback(BaseModel):
    """
    Bir çalışanın başka birine verdiği geri bildirim.
    
    reviewer  → geri bildirimi veren kişi (Employee)
    reviewee  → geri bildirimi alan kişi  (Employee)
    """
    __tablename__ = "feedbacks"

    # Kim verdi, kime verdi
    reviewer_id  = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reviewee_id  = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Geri bildirimin türü ve dönemi
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    period_date   = Column(Date, nullable=False)   # Hangi değerlendirme dönemi

    # Yapılandırılmış skorlar (1–5 arası Likert, opsiyonel)
    score_communication  = Column(Float, nullable=True)   # İletişim
    score_teamwork       = Column(Float, nullable=True)   # Takım çalışması
    score_problem_solving= Column(Float, nullable=True)   # Problem çözme
    score_leadership     = Column(Float, nullable=True)   # Liderlik
    score_technical      = Column(Float, nullable=True)   # Teknik beceri

    # Serbest metin alanları (NLP için ana hammadde)
    strength_text        = Column(Text, nullable=True)    # "En güçlü yönü nedir?"
    improvement_text     = Column(Text, nullable=True)    # "Geliştirmesi gereken alan?"
    general_comment      = Column(Text, nullable=True)    # Genel yorum

    # Speech-to-Text kaynağı mı? (Aşama 3'te kullanılacak)
    is_voice_input       = Column(Boolean, default=False)

    # Anonim mi? (peer feedback için opsiyonel)
    is_anonymous         = Column(Boolean, default=False)

    # NLP analiz sonucu — Aşama 2'de doldurulacak
    # Örnek: {"sentiment": "positive", "keywords": ["iletişim", "liderlik"], "badge_suggestion": "communicator"}
    nlp_result           = Column(JSON, nullable=True)

    # FeedbackRequest'e bağlı mı? (talep üzerine mi verildi?)
    request_id           = Column(Integer, ForeignKey("feedback_requests.id"), nullable=True)

    # İlişkiler
    reviewer    = relationship("Employee", foreign_keys=[reviewer_id],  back_populates="given_feedbacks")
    reviewee    = relationship("Employee", foreign_keys=[reviewee_id],  back_populates="received_feedbacks")
    request     = relationship("FeedbackRequest", back_populates="feedback")


# ──────────────────────────────────────────────
# MODEL 2: FeedbackRequest (Geri Bildirim Talebi)
# ──────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    """
    Bir çalışanın başka birinden feedback talep etmesi.
    requester → talep eden
    target    → feedback vermesi istenen kişi
    """
    __tablename__ = "feedback_requests"

    requester_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    target_id    = Column(Integer, ForeignKey("employees.id"), nullable=False)

    status       = Column(SQLEnum(FeedbackStatus), default=FeedbackStatus.pending, nullable=False)
    period_date  = Column(Date, nullable=False)
    deadline     = Column(Date, nullable=True)     # Son teslim tarihi
    message      = Column(String(500), nullable=True)  # Talep mesajı

    # İlişkiler
    requester = relationship("Employee", foreign_keys=[requester_id], back_populates="sent_requests")
    target    = relationship("Employee", foreign_keys=[target_id],    back_populates="received_requests")
    feedback  = relationship("Feedback", back_populates="request", uselist=False)


# ──────────────────────────────────────────────
# MODEL 3: EmployeeBadge (Çalışan Rozeti)
# ──────────────────────────────────────────────

class EmployeeBadge(BaseModel):
    """
    NLP analizi veya kural motoru tarafından çalışana atanan rozetler.
    """
    __tablename__ = "employee_badges"

    employee_id  = Column(Integer, ForeignKey("employees.id"), nullable=False)
    badge_type   = Column(SQLEnum(BadgeType),  nullable=False)
    badge_level  = Column(SQLEnum(BadgeLevel), default=BadgeLevel.bronze, nullable=False)
    period_date  = Column(Date, nullable=False)

    # Rozet hangi feedback'lerden kazanıldı? (JSON liste olarak sakla)
    # Örnek: [12, 15, 23]  → feedback id'leri
    source_feedback_ids = Column(JSON, nullable=True)

    # İlişkiler
    employee = relationship("Employee", back_populates="badges")