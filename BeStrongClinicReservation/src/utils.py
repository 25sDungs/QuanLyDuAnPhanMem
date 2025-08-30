import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.models import *

if __name__ == '__main__':
    with app.app_context():
        # print("Creating tables...")
        # db.create_all()

        print("Tables created successfully!")

        # q1 = QuyDinh(TenQuyDinh='Số Bệnh Nhân Khám', MoTa='Số Bệnh Nhân Khám Trong Ngày', GiaTri=40)
        # q2 = QuyDinh(TenQuyDinh='Số Tiền Khám', MoTa='Số Tiền Khám', GiaTri=100000)
        # db.session.add_all([q1, q2])

        u1 = User(name="NguyenDai Assmin", username='Dainy Admin', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                 user_role=UserRole.ADMIN, gender="Nam", phone='0349061851')
        db.session.add(u1)

        db.session.commit()
        print("Sample data added!")