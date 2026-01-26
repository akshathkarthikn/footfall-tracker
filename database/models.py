"""
Database models for the Footfall Tracker application.
All tables: floors, users, footfall_entries, settings, holiday_labels, audit_log
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime,
    Float, Text, ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Floor(Base):
    """Store floors that can receive footfall entries."""
    __tablename__ = 'floors'

    floor_id = Column(Integer, primary_key=True, autoincrement=True)
    floor_name = Column(String(100), nullable=False, unique=True)
    display_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("FootfallEntry", back_populates="floor")

    def __repr__(self):
        return f"<Floor(floor_id={self.floor_id}, name='{self.floor_name}')>"


class User(Base):
    """Application users with role-based access."""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='entry')  # 'entry' or 'admin'
    full_name = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    entries = relationship("FootfallEntry", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', role='{self.role}')>"

    def is_admin(self):
        return self.role == 'admin'


class FootfallEntry(Base):
    """Hourly footfall count per floor."""
    __tablename__ = 'footfall_entries'

    entry_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    hour_slot = Column(Integer, nullable=False)  # 0-23
    floor_id = Column(Integer, ForeignKey('floors.floor_id'), nullable=False)
    count = Column(Integer, nullable=False, default=0)
    entered_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    entered_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(20), default='manual')  # 'manual', 'import', 'api'
    notes = Column(Text)

    floor = relationship("Floor", back_populates="entries")
    user = relationship("User", back_populates="entries")

    __table_args__ = (
        UniqueConstraint('date', 'hour_slot', 'floor_id', name='uq_date_hour_floor'),
        Index('ix_date_floor', 'date', 'floor_id'),
    )

    def __repr__(self):
        return f"<FootfallEntry(date={self.date}, hour={self.hour_slot}, floor={self.floor_id}, count={self.count})>"


class Settings(Base):
    """Key-value store for application settings."""
    __tablename__ = 'settings'

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('users.user_id'))

    def __repr__(self):
        return f"<Settings(key='{self.key}', value='{self.value}')>"


class HolidayLabel(Base):
    """Special date labels for festivals, events, etc."""
    __tablename__ = 'holiday_labels'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    label = Column(String(100), nullable=False)
    description = Column(Text)

    def __repr__(self):
        return f"<HolidayLabel(date={self.date}, label='{self.label}')>"


class AuditLog(Base):
    """Track all changes for accountability."""
    __tablename__ = 'audit_log'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(10), nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    old_value = Column(JSON)
    new_value = Column(JSON)
    changed_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))

    __table_args__ = (
        Index('ix_audit_table_record', 'table_name', 'record_id'),
        Index('ix_audit_changed_at', 'changed_at'),
    )

    def __repr__(self):
        return f"<AuditLog(table='{self.table_name}', action='{self.action}', record={self.record_id})>"


# Default settings to be inserted on first run
DEFAULT_SETTINGS = {
    'opening_hour': '9',
    'closing_hour': '21',
    'week_start_day': '0',  # 0=Monday
    'spike_threshold_percent': '50',
    'max_footfall_value': '10000',
    'edit_window_hours': '2',
}

# Default floors to be inserted on first run
DEFAULT_FLOORS = [
    {'floor_name': 'Basement', 'display_order': 1},
    {'floor_name': 'Ground', 'display_order': 2},
    {'floor_name': 'Upper Ground', 'display_order': 3},
    {'floor_name': 'First', 'display_order': 4},
    {'floor_name': 'Second', 'display_order': 5},
    {'floor_name': 'Third', 'display_order': 6},
]
