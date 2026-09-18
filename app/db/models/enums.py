from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class SeatType(str, Enum):
    STANDARD = "standard"
    VIP = "vip"
    ACCESSIBLE = "accessible"


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventSeatStatus(str, Enum):
    AVAILABLE = "available"
    HELD = "held"
    SOLD = "sold"
    BLOCKED = "blocked"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    RESERVATION_CREATED = "reservation_created"
    RESERVATION_CONFIRMED = "reservation_confirmed"
    RESERVATION_EXPIRED = "reservation_expired"
    EVENT_REMINDER = "event_reminder"
    REPORT_READY = "report_ready"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    