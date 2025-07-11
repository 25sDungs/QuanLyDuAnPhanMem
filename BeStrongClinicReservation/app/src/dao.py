from flask_login import current_user

from app.src.models import User, QuyDinh, HoaDon, PhieuKham, Thuoc, ThuocTrongPhieuKham
from app.src.models import Arrangement, ArrList
from app import app, db, data
import hashlib

def auth_user(phone, password, role=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    u = User.query.filter(User.phone.__eq__(phone), User.password.__eq__(password))

    if role:
        u = u.filter(User.user_role.__eq__(role))

    return u.first()

def get_user_by_id(id_patient):
    return User.query.get(id_patient)

def add_user(name, username, gender, password, phone):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    u = User(name=name, username=username, gender=gender, password=password, phone=phone)

    db.session.add(u)
    db.session.commit()

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

def check_exist_arrlist(appointment_date):
    appointment_date = str(appointment_date)
    arr_lists = ArrList.query.all()
    for arr_list in arr_lists:
        arr_list.appointment_date = str(arr_list.appointment_date)
        if arr_list.appointment_date.__eq__(appointment_date):
            return True
    return False

def get_valid_id_arrlist(appointment_date):
    if check_exist_arrlist(appointment_date):
        arrlist = ArrList.query.filter(ArrList.appointment_date.__eq__(appointment_date))
        return arrlist.first().get_id()
    return None

def add_arrlist(appointment_date, patient_quantity, description):
    arr_list = ArrList(appointment_date=appointment_date,
                       patient_quantity=patient_quantity, description=description)
    db.session.add(arr_list)
    db.session.commit()
    return arr_list.id_arr_list

def add_arrangement(email, gender, name, appointment_date, address, description, id_arr_list, id_nurse=None):
    phone = current_user.phone
    id_patient = check_user_phone(phone)
    id_arr_list = get_valid_id_arrlist(appointment_date)
    result_msg = None
    patient_limit = db.session.query(QuyDinh.GiaTri).first().GiaTri
    sc_msg = None

    if id_arr_list is None:  # empty arrangement list according to date or id array list
        id_arr_list = add_arrlist(appointment_date, patient_quantity=1, description="")
        arr = Arrangement(id_arr_list=id_arr_list, id_patient=id_patient, phone=phone, email=email, gender=gender,
                          patient_name=name, appointment_date=appointment_date, address=address,
                          description=description)
        db.session.add(arr)
        db.session.commit()
        sc_msg = "Thông tin của bạn đã được ghi nhận, BeSTRONG sẽ liên hệ bạn sớm nhé!!"
    else:
        arr_list = ArrList.query.filter_by(id_arr_list=id_arr_list).first()

        if arr_list.patient_quantity >= patient_limit:
            result_msg = "Số bệnh nhân trong ngày đã vượt mức quy định của BeSTRONG, " \
                         "vui lòng chọn ngày khác bạn nhé <3"
            return result_msg, sc_msg
        else:
            arr_list.patient_quantity += 1

            arr = Arrangement(id_arr_list=id_arr_list, id_patient=id_patient, phone=phone, email=email, gender=gender,
                              patient_name=name, appointment_date=appointment_date, address=address, description=description)
            db.session.add(arr)
            db.session.commit()
            sc_msg = "Thông tin của bạn đã được ghi nhận, BeSTRONG sẽ liên hệ bạn sớm nhé!!"
    return result_msg, sc_msg