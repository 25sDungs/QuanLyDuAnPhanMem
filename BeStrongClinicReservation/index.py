from flask import render_template, request, redirect, jsonify, session
from src import dao
from app import app, login
from flask_login import login_user, logout_user, login_required, current_user

@app.route('/health')
def health_check():
    return {"status": "healthy"}

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(int(user_id))

@app.route("/")
def index():
    return render_template('MainPage/mainPage.html')

@app.route("/login", methods=['get', 'post'])
def login_process():
    err_msg = None
    err_msg1 = None
    if current_user.is_authenticated:
        return redirect('/')
    if request.method.__eq__('POST'):
        phone = request.form.get('phone')
        password = request.form.get('password')
        if not phone or not password:
            err_msg = '*Vui lòng nhập đầy đủ thông tin!!'
        else:
            user = dao.auth_user(phone=phone, password=password)
            if user:
                login_user(user=user)
                return redirect('/')
            else:
                err_msg1 = '*Số điện thoại hoặc mật khẩu KHÔNG khớp!!'

    return render_template('Login/login.html', err_msg=err_msg, err_msg1=err_msg1)

@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/')

@app.route("/register", methods=['get', 'post'])
def register_process():
    err_msg = None
    err_msg1 = None
    err_msg2 = None
    err_msg3 = None
    err_msg4 = None
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        username = request.form.get('username')
        gender = request.form.get('gender')
        fname = request.form.get('name')
        phone = request.form.get('phone')
        if not username or not fname or not gender:
            err_msg2 = '*Vui lòng nhập đầy đủ thông tin!!'
        elif not password or len(password) < 8:
            err_msg1 = '*Mật khẩu có độ dài tối thiểu là 8!!'
        elif not password.__eq__(confirm):
            err_msg = '*Mật khẩu KHÔNG khớp!!'
        elif not request.form.get('accept-terms'):
            err_msg3 = '*Bạn cần chấp nhận Điều khoản sử dụng!!'
        elif not dao.check_unique_phone(phone):
            err_msg4 = '*Số điện thoại đã được sử dụng!!'
        else:
            data = request.form.copy()

            del data['confirm']
            del data['accept-terms']
            dao.add_user(**data)
            return redirect('/login')

    return render_template('Register/register.html', err_msg=err_msg, err_msg1=err_msg1,
                           err_msg2=err_msg2, err_msg3=err_msg3, err_msg4=err_msg4)

login.login_view = 'login_process'

@app.route("/user-profile")
def user_profile():
    user_arrangements = []
    err_msg = None
    success_msg = None
    user_arrangements = dao.retrieve_user_arrangements(current_user.phone)

    return render_template('User/userProfile.html', user_arrangements=user_arrangements, err_msg=err_msg,
                           success_msg=success_msg, current_user=current_user)

@app.route("/dangKyLich", methods=['get', 'post'])
@login_required
def make_arrangement():
    err_msg = None
    sc_msg = False
    id_arr_list = None
    result_msg = None
    if request.method.__eq__('POST'):
        email = request.form.get('email')
        gender = request.form.get('gender')
        full_name = request.form.get('name')
        date = request.form.get('appointment_date')
        if not full_name or not gender or not date or not email:
            err_msg = '*Vui lòng nhập đầy đủ thông tin!!'
        else:
            data = request.form.copy()
            del data['phone']
            if dao.check_exist_arrlist(date):
                id_arr_list = dao.get_valid_id_arrlist(date)

            result_msg, sc_msg = dao.add_arrangement(id_arr_list=id_arr_list, **data)

    return render_template('MakeArrangement/ArrangementRegister.html', err_msg=err_msg, sc_msg=sc_msg, result_msg=result_msg)

@app.route("/specialists", methods=['get'])
def get_specialists():
    return render_template('Specialists/specialistPage.html')


@app.route("/specialists/<int:doctor_id>", methods=['GET', 'POST'])
def doctor_profile(doctor_id):
    hoso = utils.get_profile_link(doctor_id)
    if hoso:
        return redirect(hoso)

    doctor = dao.get_doctor_by_id(doctor_id)
    return render_template('Specialists/doctorProfile.html', doctor=doctor, doctor_id=doctor_id)


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
