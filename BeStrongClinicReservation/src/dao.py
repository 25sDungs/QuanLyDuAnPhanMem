from flask_login import current_user

from src.models import User, QuyDinh, Arrangement, Doctor, HoSo, Doctor_Schedule
from src.models import UserRole
from app import app, db
import hashlib
from datetime import datetime

def auth_user(phone, password, role=None):
    try:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        u = User.query.filter(User.phone == phone, User.password == password)
        if role:
            u = u.filter(User.user_role == role)
        return u.first()
    except Exception as e:
        print(f"Authentication error: {e}")
        return None


def get_user_by_id(id_patient):
    return User.query.get(id_patient)


def get_doctor_by_id(id):
    return Doctor.query.get(id)


def add_user(name, username, gender, password, phone):
    try:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        u = User(name=name, username=username, gender=gender, password=password, phone=phone)

        db.session.add(u)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Cannot add user because of error: {e}")
        return False


def check_user_phone(phone):
    u = User.query.filter(User.phone.__eq__(phone))
    return u.first().get_id()


def check_user_username(username):
    u = User.query.filter(User.username.__eq__(username))
    return u.first().get_id()


def check_unique_phone(phone):
    user = db.session.query(User).filter_by(phone=phone).first()

    return user is None


def retrieve_user_arrangements(phone=None, username=None):
    query = Arrangement.query

    if phone:
        query = Arrangement.query.filter(Arrangement.phone.__eq__(phone))
        return query.all()
    elif username:
        id_patient = check_user_username(username)
        query = Arrangement.query.filter(Arrangement.id_patient.__eq__(id_patient))
        return query.all()

    return None


def add_arrangement(email, gender, name, appointment_date, address, description, phone, username, status):
    if not phone:
        phone = current_user.phone
        id_patient = check_user_phone(phone)
    else:
        id_patient = check_user_username(username)
    result_msg = None
    patient_limit = db.session.query(QuyDinh.GiaTri).first().GiaTri
    sc_msg = None
    arr = Arrangement(id_patient=id_patient, phone=phone, email=email, gender=gender,
                      patient_name=name, appointment_date=appointment_date, address=address,
                      description=description, status=status)
    db.session.add(arr)
    db.session.commit()
    sc_msg = "Thông tin của bạn đã được ghi nhận, BeSTRONG sẽ liên hệ bạn sớm nhé!!"
    appointment_id = arr.id_arrangement
    return appointment_id, result_msg, sc_msg


def update_appointment_status(appointment_id, status):
    appointment = db.session.query(Arrangement).filter_by(id_arrangement=appointment_id).first()
    if not appointment:
        return

    appointment.status = status
    db.session.commit()

    return appointment_id


def get_profile_link(id):
    hoso = HoSo.query.filter_by(BacSi_id=id).first()
    return hoso.link_profile if hoso else None


def load_specialists():
    query = db.session.query(Doctor)
    return query.all()


def get_doctor_schedules(doctor_id):
    try:
        schedules = Doctor_Schedule.query.filter_by(
            BacSi_id=doctor_id,
            TrangThai=True
        ).order_by(Doctor_Schedule.Thu, Doctor_Schedule.Buoi).all()
        return schedules
    except Exception as e:
        print(f"Error getting doctor schedules: {e}")
        return []


def get_available_time_slots(doctor_id):
    try:
        slots = []
        thu_names = {2: 'Thứ 2', 3: 'Thứ 3', 4: 'Thứ 4', 5: 'Thứ 5', 6: 'Thứ 6', 7: 'Thứ 7', 8: 'Chủ nhật'}
        buoi_options = ['Sang', 'Chieu']

        for thu in range(2, 9):
            for buoi in buoi_options:
                existing = Doctor_Schedule.query.filter_by(
                    BacSi_id=doctor_id,
                    Thu=thu,
                    Buoi=buoi,
                    TrangThai=True
                ).first() if doctor_id else None

                slots.append({
                    'thu': thu,
                    'thu_name': thu_names[thu],
                    'buoi': buoi,
                    'is_selected': existing is not None,
                    'schedule_id': existing.ID if existing else None
                })

        return slots
    except Exception as e:
        print(f"Error getting available time slots: {e}")
        return []


def add_doctor_schedule(doctor_id, thu, buoi):
    try:
        existing = Doctor_Schedule.query.filter_by(
            BacSi_id=doctor_id,
            Thu=thu,
            Buoi=buoi
        ).first()

        if existing:
            if existing.TrangThai:
                return False,
            else:
                existing.TrangThai = True
                existing.NgayCapNhat = datetime.utcnow()
                db.session.commit()
                return True,

        new_schedule = Doctor_Schedule(
            BacSi_id=doctor_id,
            Thu=thu,
            Buoi=buoi,
            TrangThai=True
        )

        db.session.add(new_schedule)
        db.session.commit()
        return True, "Đã thêm lịch làm việc thành công"

    except Exception as e:
        db.session.rollback()
        print(f"Error adding doctor schedule: {e}")
        return False, f"Lỗi khi thêm lịch: {str(e)}"


def remove_doctor_schedule(doctor_id, schedule_id):
    try:
        schedule = Doctor_Schedule.query.filter_by(
            ID=schedule_id,
            BacSi_id=doctor_id
        ).first()

        if not schedule:
            return False, "Không tìm thấy lịch làm việc"

        schedule.TrangThai = False
        schedule.NgayCapNhat = datetime.utcnow()
        db.session.commit()

        return True, "Đã xóa lịch làm việc thành công"

    except Exception as e:
        db.session.rollback()
        print(f"Error removing doctor schedule: {e}")
        return False, f"Lỗi khi xóa lịch: {str(e)}"


def get_doctor_working_days_summary(doctor_id):
    try:
        schedules = get_doctor_schedules(doctor_id)

        working_days = {}
        for schedule in schedules:
            thu_name = schedule.get_thu_name()
            if thu_name not in working_days:
                working_days[thu_name] = []
            working_days[thu_name].append(schedule.Buoi)

        ordered_days = []
        day_order = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']

        for day in day_order:
            if day in working_days:
                ordered_days.append({
                    'day': day,
                    'shifts': working_days[day]
                })

        return ordered_days
    except Exception as e:
        print(f"Error getting working days summary: {e}")
        return []



def get_all_doctors():
    try:
        doctors = User.query.filter(User.user_role == UserRole.DOCTOR).all()
        return doctors
    except Exception as e:
        print(f"Error getting all doctors: {e}")
        return []