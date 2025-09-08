from models import *
from datetime import datetime, timedelta
from sqlalchemy import func

current_year = datetime.now().year
one_year_ago = datetime.now() - timedelta(days=365)
start_of_year = datetime(current_year, 1, 1)
end_of_year = datetime(current_year, 12, 31)

trienkham = db.session.query(QuyDinh).filter_by(ID=2).first().GiaTri

def get_profile_link(id):
    hoso = HoSo.query.filter_by(BacSi_id=id).first()
    return hoso.link_profile if hoso else None


def load_specialists():
    query = db.session.query(Doctor)
    return query.all()


def revenue_stats_by_month(year):
    p = (db.session.query(
        func.month(Arrangement.appointment_date),
        func.count(Arrangement.id_arrangement),
        (func.count(Arrangement.id_arrangement) * trienkham))
         .filter(func.year(Arrangement.appointment_date) == year)
         .group_by(func.month(Arrangement.appointment_date))
         .order_by(func.month(Arrangement.appointment_date))
         )
    return p.all()


def revenue_stats(month, from_date, to_date):
    p = (
        db.session.query(
            func.date(Arrangement.appointment_date),
            func.count(Arrangement.id_arrangement),
            (func.count(Arrangement.id_arrangement) * trienkham))
        .group_by(func.date(Arrangement.appointment_date))
        .order_by(func.date(Arrangement.appointment_date))
    )
    if month:
        p = p.filter(func.month(Arrangement.appointment_date) == month,
                     func.year(Arrangement.appointment_date) == current_year,
                     Arrangement.appointment_date.__ge__(one_year_ago))
    if from_date:
        p = p.filter(Arrangement.appointment_date.__ge__(from_date))
    if to_date:
        p = p.filter(Arrangement.appointment_date.__le__(to_date))

    return p.all()


def sum_revenue(lists):
    s = 0
    for i in lists:
        s += i[-1]
    return s


if __name__ == '__main__':
    with app.app_context():
        print("Creating tables...")
        db.create_all()

        print("Tables created successfully!")

        db.session.commit()
        print("Sample data added!")
