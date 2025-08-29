import sys
import os
from datetime import datetime, timedelta
sys.path.append('/src')
from src.models import Arrangement
import json


def get_valid_arrangements():
    today = datetime.now().date()
    next_day = today + timedelta(days=1)
    next_day = str(next_day)
    arrangements = Arrangement.query.all()
    valid_arrangements = []
    for arr in arrangements:
        arr.appointment_date = str(arr.appointment_date)
        if arr.appointment_date.__eq__(next_day):
            valid_arrangements.append(arr)
    return valid_arrangements


def save_arrangements_to_json():
    valid_arrangements = get_valid_arrangements()

    arrangements_data = {
        "sum_number_of_arrangements": len(valid_arrangements),
        "arrangements": []
    }

    for arr in valid_arrangements:
        arrangements_data["arrangements"].append({
            "email": arr.email,
            "patient_name": arr.patient_name,
            "phone": arr.phone,
            "appointment_date": arr.appointment_date
        })

    output_file = "/data/arrangements.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(arrangements_data, file, indent=4, ensure_ascii=False)

    print(f"Valid arrangements saved to {output_file}")


save_arrangements_to_json()