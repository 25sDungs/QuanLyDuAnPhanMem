import os
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta

from authlib.integrations.flask_client import OAuth
from src.models import Doctor_Schedule
from src.dao import (auth_user, get_available_time_slots, add_doctor_schedule,
                     remove_doctor_schedule, get_doctor_working_days_summary, get_pending_schedules,
                     approve_schedule, reject_schedule, get_schedule_statistics)

from src.models import User, QuyDinh, Arrangement
from dotenv import load_dotenv
from flask import render_template, request, redirect, jsonify, session, url_for, flash
from src import dao
from app import app, login, db
from flask_login import login_user, logout_user, login_required, current_user

load_dotenv()


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
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        if not phone or not password:
            err_msg = '*Vui lòng nhập đầy đủ thông tin!!'
        else:
            user = auth_user(phone=phone, password=password)
            if user:
                login_user(user)
                return redirect('/')
            else:
                err_msg1 = '*Số điện thoại hoặc mật khẩu KHÔNG khớp!!'

    return render_template('Login/login.html', err_msg=err_msg, err_msg1=err_msg1)


@app.route("/work-schedule", methods=['GET', 'POST'])
@login_required
def work_schedule():
    doctor_id = current_user.id_patient
    working_days_summary = get_doctor_working_days_summary(doctor_id)
    available_time_slots = get_available_time_slots(doctor_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            thu = request.form.get('thu')
            buoi = request.form.get('buoi')

            if not thu or not buoi:
                flash('Thiếu thông tin ngày và buổi làm việc!', 'error')
            else:
                try:
                    thu = int(thu)
                    success, message = add_doctor_schedule(doctor_id, thu, buoi)
                    if success:
                        flash('Đã thêm lịch làm việc thành công!', 'success')
                    else:
                        flash(message or 'Có lỗi khi thêm lịch làm việc!', 'error')
                except ValueError:
                    flash('Thông tin ngày không hợp lệ!', 'error')

        elif action == 'remove':
            schedule_id = request.form.get('schedule_id')

            if not schedule_id:
                flash('Thiếu thông tin lịch cần xóa!', 'error')
            else:
                try:
                    schedule_id = int(schedule_id)
                    success, message = remove_doctor_schedule(doctor_id, schedule_id)
                    if success:
                        flash('Đã xóa lịch làm việc thành công!', 'success')
                    else:
                        flash(message or 'Có lỗi khi xóa lịch làm việc!', 'error')
                except ValueError:
                    flash('ID lịch không hợp lệ!', 'error')

        return redirect(url_for('work_schedule'))

    return render_template('Doctor/lichLamViec.html',
                           working_days_summary=working_days_summary,
                           available_time_slots=available_time_slots,
                           current_doctor=current_user)


# ADMIN
@app.route("/schedule-management", methods=['GET', 'POST'])
@login_required
def admin_schedule_management():
    stats = get_schedule_statistics()

    pending_schedules = get_pending_schedules()

    if request.method == 'POST':
        action = request.form.get('action')
        schedule_id = request.form.get('schedule_id')

        if not schedule_id:
            flash('Thiếu thông tin lịch làm việc!', 'error')
        else:
            try:
                schedule_id = int(schedule_id)
                admin_id = current_user.id_patient

                if action == 'approve':
                    success, message = approve_schedule(schedule_id, admin_id)
                    if success:
                        flash('Đã duyệt lịch làm việc thành công!', 'success')
                    else:
                        flash(message or 'Có lỗi khi duyệt lịch làm việc!', 'error')

                elif action == 'reject':
                    reason = request.form.get('reason')
                    if not reason or not reason.strip():
                        flash('Vui lòng nhập lý do từ chối!', 'error')
                    else:
                        success, message = reject_schedule(schedule_id, admin_id, reason.strip())
                        if success:
                            flash('Đã từ chối lịch làm việc!', 'error')
                        else:
                            flash(message or 'Có lỗi khi từ chối lịch làm việc!', 'error')

            except ValueError:
                flash('ID lịch không hợp lệ!', 'error')

        return redirect(url_for('admin_schedule_management'))

    next_week_start = Doctor_Schedule.get_next_week_start()
    week_range = Doctor_Schedule.get_week_range_text(next_week_start)

    return render_template('admin/scheduleManagement.html',
                           stats=stats,
                           pending_schedules=pending_schedules,
                           week_range=week_range,
                           current_user=current_user)


@app.route("/schedule-management/approve/<int:schedule_id>", methods=['POST'])
@login_required
def approve_schedule_ajax(schedule_id):
    try:
        admin_id = current_user.id_patient
        success, message = approve_schedule(schedule_id, admin_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Đã duyệt lịch làm việc thành công!'
            })
        else:
            return jsonify({
                'success': False,
                'message': message or 'Có lỗi khi duyệt lịch làm việc!'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        }), 500


@app.route("/schedule-management/reject/<int:schedule_id>", methods=['POST'])
@login_required
def reject_schedule_ajax(schedule_id):
    try:
        data = request.get_json()
        reason = data.get('reason', '').strip() if data else ''

        if not reason:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập lý do từ chối!'
            })

        admin_id = current_user.id_patient
        success, message = reject_schedule(schedule_id, admin_id, reason)

        if success:
            return jsonify({
                'success': True,
                'message': 'Đã từ chối lịch làm việc!'
            })
        else:
            return jsonify({
                'success': False,
                'message': message or 'Có lỗi khi từ chối lịch làm việc!'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        }), 500


@app.route("/schedule-management/stats", methods=['GET'])
@login_required
def get_schedule_stats():
    try:
        stats = get_schedule_statistics()
        if stats:
            return jsonify({
                'success': True,
                'data': stats
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Không thể lấy thống kê'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        }), 500


@app.route("/schedule-management/pending", methods=['GET'])
@login_required
def get_pending_schedules_ajax():
    try:
        pending_schedules = get_pending_schedules()
        schedules_data = []

        for schedule in pending_schedules:
            schedules_data.append({
                'id': schedule.ID,
                'doctor_name': schedule.bac_si.name if schedule.bac_si.name else schedule.bac_si.username,
                'doctor_username': schedule.bac_si.username,
                'day': schedule.get_thu_name(),
                'shift': 'Buổi sáng' if schedule.Buoi == 'Sang' else 'Buổi chiều',
                'shift_type': schedule.Buoi,
                'created_date': schedule.NgayTao.strftime('%d/%m/%Y %H:%M') if schedule.NgayTao else '',
                'doctor_initials': ''.join(
                    [word[0].upper() for word in (schedule.bac_si.name or schedule.bac_si.username).split()[:2]])
            })

        return jsonify({
            'success': True,
            'data': schedules_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        }), 500


@app.route("/register", methods=['GET', 'POST'])
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
    err_msg = None
    success_msg = None
    user_arrangements = dao.retrieve_user_arrangements(username=current_user.username)
    print(user_arrangements)
    return render_template('User/userProfile.html', user_arrangements=user_arrangements, err_msg=err_msg,
                           success_msg=success_msg, current_user=current_user)


VNPAY_TMN_CODE = os.getenv('VNP_TMNCODE')
VNPAY_HASH_SECRET = os.getenv('VNP_HASHSECRET')
VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNPAY_RETURN_URL = 'http://127.0.0.1:8080/vnpay/return'
VNPAY_IPN_URL = 'http://127.0.0.1:8080/vnpay/ipn'


@app.route("/dangKyLich", methods=['GET', 'POST'])
@login_required
def make_arrangement():
    err_msg = None
    sc_msg = False
    result_msg = None
    if request.method == 'POST':
        phone = request.form.get('phone')
        email = request.form.get('email')
        gender = request.form.get('gender')
        full_name = request.form.get('name')
        date = request.form.get('appointment_date')
        if not full_name or not gender or not date or not email or not phone:
            err_msg = '*Vui lòng nhập đầy đủ thông tin!!'
        else:
            data = request.form.copy()
            appointment_id, result_msg, sc_msg = dao.add_arrangement(**data, username=current_user.username,
                                                                     status='pending')
            if sc_msg:
                amount = db.session.query(QuyDinh).filter_by(ID=2).first().GiaTri
                vnp_params = {
                    'vnp_Version': '2.1.0',
                    'vnp_Command': 'pay',
                    'vnp_TmnCode': VNPAY_TMN_CODE,
                    'vnp_Amount': amount * 100,
                    'vnp_CurrCode': 'VND',
                    'vnp_TxnRef': str(appointment_id),
                    'vnp_OrderInfo': f'Thanh toan lich kham ID: {appointment_id}',
                    'vnp_OrderType': 'other',
                    'vnp_Locale': 'vn',
                    'vnp_ReturnUrl': VNPAY_RETURN_URL,
                    'vnp_IpAddr': request.remote_addr,
                    'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
                    'vnp_ExpireDate': (datetime.now() + timedelta(minutes=15)).strftime('%Y%m%d%H%M%S')
                }
                sorted_params = sorted(vnp_params.items())
                query_string = urllib.parse.urlencode(sorted_params)
                hash_data = query_string.encode('utf-8')
                secure_hash = hmac.new(
                    VNPAY_HASH_SECRET.encode('utf-8'),
                    hash_data,
                    hashlib.sha512
                ).hexdigest()
                vnp_params['vnp_SecureHash'] = secure_hash
                vnpay_url = f"{VNPAY_URL}?{query_string}&vnp_SecureHash={secure_hash}"
                return redirect(vnpay_url)
            else:
                err_msg = result_msg or 'Lỗi khi lưu lịch khám, vui lòng thử lại!'

    return render_template('MakeArrangement/ArrangementRegister.html',
                           err_msg=err_msg,
                           sc_msg=sc_msg,
                           result_msg=result_msg)


@app.route("/vnpay/return")
def payment_return():
    vnp_params = request.args.to_dict()
    secure_hash = vnp_params.pop('vnp_SecureHash', None)
    vnp_params.pop('vnp_SecureHashType', None)

    sorted_params = sorted(vnp_params.items())
    query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote_plus)
    hash_data = query_string.encode('utf-8')

    calculated_hash = hmac.new(
        VNPAY_HASH_SECRET.encode('utf-8'),
        hash_data,
        hashlib.sha512
    ).hexdigest()

    appointment_id = vnp_params.get('vnp_TxnRef')

    if calculated_hash != secure_hash:
        flash("Dữ liệu thanh toán không hợp lệ, vui lòng thử lại!", "danger")
        return redirect("/dangKyLich")

    if vnp_params.get('vnp_ResponseCode') == '00':
        dao.update_appointment_status(appointment_id=appointment_id, status='confirmed')
        flash("Thanh toán thành công! Lịch khám của bạn đã được xác nhận.", "success")
        return redirect("/user-profile")
    else:
        dao.update_appointment_status(appointment_id=appointment_id, status='failed')
        flash("Hủy thanh toán!", "warning")
        return redirect("/dangKyLich")


oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

facebook = oauth.register(
    name='facebook',
    client_id=os.getenv('FACEBOOK_CLIENT_ID'),
    client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
    authorize_url='https://www.facebook.com/dialog/oauth',
    access_token_url='https://graph.facebook.com/oauth/access_token',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email public_profile'}
)


@app.route('/google/')
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri, prompt="select_account")


@app.route('/google/auth/')
def google_auth():
    try:
        print(f"Session at Google auth: {session}")
        token = google.authorize_access_token()
        nonce = session.pop('google_nonce', None)
        user_info = google.parse_id_token(token, nonce=nonce)
        print(f"Google User Info: {user_info}")
        email = user_info['email']
        name = user_info['name']
        username = email.split('@')[0]
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(name=name, username=username, gender='', password='', phone='', user_role='user')
            db.session.add(user)
            db.session.commit()

        login_user(user)
        session['user'] = {'username': username, 'name': name}
        return redirect('/')
    except Exception as e:
        return f"Error: {str(e)}", 400


@app.route('/facebook/')
def facebook_login():
    redirect_uri = url_for('facebook_auth', _external=True)
    return facebook.authorize_redirect(redirect_uri)


@app.route('/facebook/auth/')
def facebook_auth():
    try:
        token = facebook.authorize_access_token()
        resp = facebook.get('me?fields=id,name,email')
        user_info = resp.json()
        email = user_info.get('email')
        name = user_info.get('name')
        user = User.query.filter_by(username=email).first()

        if not user:
            user = User(name=name, username=email, gender='', password='', phone='')
            db.session.add(user)
            db.session.commit()

        login_user(user)
        session['user'] = {'username': email, 'name': name}
        return redirect('/')
    except Exception as e:
        return f"Facebook Auth Error: {str(e)}", 400


@app.route('/logout')
def logout():
    logout_user()
    session.pop('user', None)
    return redirect('/')


@app.route("/cancel_arrangement/<int:arrangement_id>", methods=["POST"])
@login_required
def cancel_arrangement(arrangement_id):
    arrangement = Arrangement.query.get(arrangement_id)
    arrangement.status = "cancelled"
    db.session.commit()
    return redirect("/user-profile")


@app.route("/specialists", methods=['get'])
def get_specialists():
    specialists = dao.load_specialists()
    return render_template('Specialists/specialistPage.html', specialists=specialists)


@app.route("/specialists/<int:doctor_id>", methods=['GET', 'POST'])
def doctor_profile(doctor_id):
    hoso = utils.get_profile_link(doctor_id)
    if hoso:
        return redirect(hoso)

    doctor = dao.get_doctor_by_id(doctor_id)
    return render_template('Specialists/doctorProfile.html', doctor=doctor, doctor_id=doctor_id)


@app.route("/login-admin", methods=['post'])
def login_admin():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        if phone and password:
            user = auth_user(phone=phone, password=password)
            if user:
                login_user(user)
            return redirect("/admin")

    return redirect("/login")


if __name__ == '__main__':
    from src import admin

    app.run(host='localhost', port=8081, debug=True)
