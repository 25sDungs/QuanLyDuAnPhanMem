import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from flask import redirect, request
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from src.models import QuyDinh, User, Doctor, HoSo, Arrangement
from flask_login import current_user, logout_user
import hashlib

admin = Admin(app=app, name='BeStrong', template_mode='bootstrap4')


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()


class DoctorView(AdminView):
    column_list = ['name', 'username', 'phone', 'chungChi', 'HocVi', 'SoGioLamViec', 'KinhNghiem', 'DanhGia']
    column_searchable_list = ['name']
    column_editable_list = ['name', 'phone', 'chungChi', 'HocVi', 'KinhNghiem']

    def on_model_change(self, form, model, is_created):
        if is_created:
            raw_password = form.password.data.strip()
            model.password = hashlib.md5(raw_password.encode('utf-8')).hexdigest()

    def after_model_change(self, form, model, is_created):
        if is_created:
            profile = HoSo(
                link_profile=f"/specialists/{model.id_doctor}",
                BacSi_id=model.id_doctor
            )
            db.session.add(profile)
            db.session.commit()


class ProfileView(AdminView):
    column_searchable_list = ['BacSi_id']
    column_editable_list = ['link_profile']


class QuyDinhView(AdminView):
    column_list = ['ID', 'TenQuyDinh', 'GiaTri', 'MoTa']
    column_searchable_list = ['TenQuyDinh']
    column_editable_list = ['GiaTri']


class ArrangementView(AdminView):
    column_list = ['email', 'patient_name', 'appointment_date', 'status', 'address', 'description']
    column_searchable_list = ['patient_name']
    column_editable_list = ['status']


class UserView(AdminView):
    column_list = ['id', 'username', 'user_role', 'phone']
    column_searchable_list = ['username', 'phone']
    column_editable_list = ['user_role']

    def on_model_change(self, form, model, is_created):
        if is_created:
            raw_password = form.password.data.strip()
            model.password = hashlib.md5(raw_password.encode('utf-8')).hexdigest()


class BaseAdminView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()


class StatsView(BaseAdminView):
    @expose("/")
    def index(self):
        month = request.args.get('ThangThongKe')
        year = request.args.get('NamThongKe')
        type_stats = request.args.get('LoaiThongKe')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        if year and type_stats == 'Revenue':
            rstats = utils.revenue_stats_by_month(year=year)
            return self.render('admin/stats.html', sum=utils.sum_revenue(rstats), rstats_year=rstats)

        elif type_stats == 'Revenue':
            rstats = utils.revenue_stats(month=month, from_date=from_date, to_date=to_date)
            return self.render('admin/stats.html', sum=utils.sum_revenue(rstats), rstats=rstats)

        return self.render('admin/stats.html')


class LogoutView(BaseAdminView):
    @expose('/')
    def __index__(self):
        logout_user()
        return redirect('/admin')


admin.add_view(UserView(User, db.session))
admin.add_view(ArrangementView(Arrangement, db.session))
admin.add_view(DoctorView(Doctor, db.session))
admin.add_view(ProfileView(HoSo, db.session))
admin.add_view(QuyDinhView(QuyDinh, db.session))
admin.add_view(StatsView(name='Thống Kê'))
admin.add_view(LogoutView(name='Đăng Xuất'))