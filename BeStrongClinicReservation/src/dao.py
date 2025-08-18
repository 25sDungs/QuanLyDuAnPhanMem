from flask_login import current_user

from src.models import User, QuyDinh, Arrangement
from app import app, db
import hashlib


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


def check_unique_phone(phone):
    user = db.session.query(User).filter_by(phone=phone).first()

    return user is None


def retrieve_user_arrangements(phone):
    query = Arrangement.query

    if phone:
        query = Arrangement.query.filter(Arrangement.phone.__eq__(phone))
        return query.all()

    return None


def add_arrangement(email, gender, name, appointment_date, address, description, status):
    phone = current_user.phone
    id_patient = check_user_phone(phone)
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
