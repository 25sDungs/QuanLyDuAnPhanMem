from src.models import *


def get_profile_link(id):
    hoso = HoSo.query.filter_by(BacSi_id=id).first()
    return hoso.link_profile if hoso else None


def load_specialists():
    query = db.session.query(Doctor)
    return query.all()
