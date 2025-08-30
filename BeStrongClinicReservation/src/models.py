import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, Date, DateTime
from sqlalchemy.orm import relationship
from app import db, app
from enum import Enum as RoleEnum
from flask_login import UserMixin
import pymysql
import os
import hashlib
from enum import Enum as PyEnum
from datetime import datetime, timedelta

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_CONNECTION_NAME = os.getenv('DB_CONNECTION_NAME')


class UserRole(RoleEnum):
    ADMIN = 1
    USER = 2  # Patient
    DOCTOR = 3


class ScheduleStatus(PyEnum):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3


class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id_patient = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    gender = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=False, unique=True)
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    arrangement = relationship('Arrangement', backref='user', lazy=True)  # Backref tới bảng Arrangement

    def get_id(self):
        return self.id_patient

    def is_doctor(self):
        return self.user_role == UserRole.DOCTOR

    def is_user(self):
        return self.user_role == UserRole.USER

    def is_admin(self):
        return self.user_role == UserRole.ADMIN


class Admin(User):
    __tablename__ = 'Administrator'
    id_admin = Column(Integer, ForeignKey(User.id_patient), primary_key=True, nullable=False)
    QuyenHan = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
        'inherit_condition': id_admin == User.id_patient,
    }


class Doctor(User):
    __tablename__ = 'Doctor'
    id_doctor = Column(Integer, ForeignKey(User.id_patient), primary_key=True, nullable=False)
    chungChi = Column(String(50))
    HocVi = Column(String(50))
    SoGioLamViec = Column(Integer)
    KinhNghiem = Column(String(50))
    DanhGia = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'doctor',
        'inherit_condition': id_doctor == User.id_patient,
    }


class LichLamViec(db.Model):
    __tablename__ = 'WorkSchedule'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Ngay = Column(Date)
    GioBatDau = Column(DateTime)
    GioKetThuc = Column(DateTime)
    IsLamNgoaiGio = Column(Boolean)
    HuyLich = Column(Boolean)
    BacSi_id = Column(Integer, ForeignKey(Doctor.id_doctor), nullable=True)

    def huy_lich(self):
        self.HuyLich = True


class Doctor_Schedule(db.Model):
    __tablename__ = 'Doctor_Schedule'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    BacSi_id = Column(Integer, ForeignKey('User.id_patient'), nullable=False)
    Thu = Column(Integer, nullable=False)
    Buoi = Column(String(10), nullable=False)
    TrangThai = Column(Boolean, default=True)
    TrangThaiDuyet = Column(Enum(ScheduleStatus), default=ScheduleStatus.PENDING)
    TuanLamViec = Column(Date, nullable=False)
    LyDoTuChoi = Column(String(200), nullable=True)
    NgayDuyet = Column(DateTime, nullable=True)
    NguoiDuyet_id = Column(Integer, ForeignKey('User.id_patient'), nullable=True)

    NgayTao = Column(DateTime, default=datetime.utcnow)
    NgayCapNhat = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bac_si = relationship("Doctor", backref="lich_lam_viec", foreign_keys=[BacSi_id])
    nguoi_duyet = relationship("User", foreign_keys=[NguoiDuyet_id])

    def __repr__(self):
        thu_names = {2: 'Thứ 2', 3: 'Thứ 3', 4: 'Thứ 4', 5: 'Thứ 5', 6: 'Thứ 6', 7: 'Thứ 7', 8: 'Chủ nhật'}
        return f"<Doctor_Schedule {self.bac_si.username if self.bac_si else 'Unknown'} - {thu_names.get(self.Thu)} - {self.Buoi}>"

    def get_thu_name(self):
        thu_names = {2: 'Thứ 2', 3: 'Thứ 3', 4: 'Thứ 4', 5: 'Thứ 5', 6: 'Thứ 6', 7: 'Thứ 7', 8: 'Chủ nhật'}
        return thu_names.get(self.Thu, 'Không xác định')

    def get_status_text(self):
        status_map = {
            ScheduleStatus.PENDING: 'Chờ duyệt',
            ScheduleStatus.APPROVED: 'Đã duyệt',
            ScheduleStatus.REJECTED: 'Từ chối'
        }
        return status_map.get(self.TrangThaiDuyet, 'Không xác định')

    def get_status_class(self):
        status_class_map = {
            ScheduleStatus.PENDING: 'pending',
            ScheduleStatus.APPROVED: 'approved',
            ScheduleStatus.REJECTED: 'rejected'
        }
        return status_class_map.get(self.TrangThaiDuyet, 'pending')

    def toggle_trang_thai(self):
        self.TrangThai = not self.TrangThai
        self.NgayCapNhat = datetime.utcnow()

    def approve(self, admin_id):
        self.TrangThaiDuyet = ScheduleStatus.APPROVED
        self.NgayDuyet = datetime.utcnow()
        self.NguoiDuyet_id = admin_id
        self.NgayCapNhat = datetime.utcnow()

    def reject(self, admin_id, reason=None):
        self.TrangThaiDuyet = ScheduleStatus.REJECTED
        self.NgayDuyet = datetime.utcnow()
        self.NguoiDuyet_id = admin_id
        self.LyDoTuChoi = reason
        self.NgayCapNhat = datetime.utcnow()

    @staticmethod
    def get_current_week_start():
        today = datetime.now().date()
        days_ahead = today.weekday()
        monday = today - timedelta(days=days_ahead)
        return monday

    @staticmethod
    def get_next_week_start():
        current_monday = Doctor_Schedule.get_current_week_start()
        return current_monday + timedelta(days=7)

    @staticmethod
    def get_week_range_text(start_date):
        end_date = start_date + timedelta(days=6)
        return f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

    @staticmethod
    def cleanup_old_schedules():
        current_week = Doctor_Schedule.get_current_week_start()
        old_schedules = Doctor_Schedule.query.filter(
            Doctor_Schedule.TuanLamViec < current_week
        ).all()

        for schedule in old_schedules:
            db.session.delete(schedule)

        db.session.commit()
        return len(old_schedules)

    @staticmethod
    def get_available_slots(doctor_id=None, week_start=None):
        if week_start is None:
            week_start = Doctor_Schedule.get_next_week_start()

        slots = []
        thu_names = {2: 'Thứ 2', 3: 'Thứ 3', 4: 'Thứ 4', 5: 'Thứ 5', 6: 'Thứ 6', 7: 'Thứ 7', 8: 'Chủ nhật'}
        buoi_options = ['Sang', 'Chieu']

        for thu in range(2, 9):
            for buoi in buoi_options:
                existing = Doctor_Schedule.query.filter_by(
                    BacSi_id=doctor_id,
                    Thu=thu,
                    Buoi=buoi,
                    TuanLamViec=week_start,
                    TrangThai=True
                ).first() if doctor_id else None

                slots.append({
                    'thu': thu,
                    'thu_name': thu_names[thu],
                    'buoi': buoi,
                    'is_selected': existing is not None,
                    'schedule_id': existing.ID if existing else None,
                    'week_start': week_start
                })

        return slots


class QuyDinh(db.Model):
    __tablename__ = 'Rule'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    TenQuyDinh = Column(String(50), nullable=False, unique=True)
    GiaTri = Column(Integer)
    MoTa = Column(String(100))


class HoSo(db.Model):
    __tablename__ = 'Profile'
    id_profile = Column(Integer, primary_key=True, autoincrement=True)
    link_profile = Column(String(50))
    BacSi_id = Column(Integer, ForeignKey(Doctor.id_doctor), nullable=True)


class Arrangement(db.Model):
    __tablename__ = 'Arrangement'
    id_arrangement = Column(Integer, primary_key=True, autoincrement=True)
    id_patient = Column(Integer, ForeignKey(User.id_patient), nullable=False)  # Khóa ngoại tham chiếu User.id_patient
    phone = Column(String(20), nullable=False)
    email = Column(String(50), nullable=False)
    gender = Column(String(50), nullable=False)
    patient_name = Column(String(50), nullable=False)
    appointment_date = Column(Date, nullable=False)
    address = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)

    def to_dict(self):
        return {
            'id_arrangement': self.id_arrangement,
            'patient_name': self.patient_name,
            'gender': self.gender,
            'phone': self.phone,
            'address': self.address
        }


if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        # u = User(username='admin', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
        #          user_role=UserRole.ADMIN, gender="Nam", phone='0000000000')
        # db.session.add(u)
        # q1 = QuyDinh(TenQuyDinh='Số Bệnh Nhân Khám', MoTa='Số Bệnh Nhân Khám Trong Ngày', GiaTri=40)
        # q2 = QuyDinh(TenQuyDinh='Số Tiền Khám', MoTa='Số Tiền Khám', GiaTri=100000)
        # db.session.add_all([q1, q2])
        # ngaypk1 = datetime(2024, 12, 6)
        # pk1 = PhieuKham(NgayLapPhieu=ngaypk1, HoaDon_ID=1)
        # ngaypk2 = datetime(2024, 11, 14)
        # pk2 = PhieuKham(NgayLapPhieu=ngaypk2, HoaDon_ID=2)
        # ngaypk3 = datetime(2024, 12, 19)
        # pk3 = PhieuKham(NgayLapPhieu=ngaypk3, HoaDon_ID=3)
        # ngaypk4 = datetime(2024, 10, 6)
        # pk4 = PhieuKham(NgayLapPhieu=ngaypk1, HoaDon_ID=4)
        # ngaypk5 = datetime(2024, 9, 14)
        # pk5 = PhieuKham(NgayLapPhieu=ngaypk2, HoaDon_ID=5)
        # ngaypk6 = datetime(2024, 12, 19)
        # pk6 = PhieuKham(NgayLapPhieu=ngaypk3, HoaDon_ID=6)
        # db.session.add_all([pk1, pk2, pk3, pk4, pk5, pk6])

        u = User(name="Huu Khang Doctor", username='Khang Doctor', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                 user_role=UserRole.DOCTOR, gender="Nam", phone='0903021744')
        db.session.add(u)
        db.session.commit()