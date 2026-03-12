import streamlit as st
import pandas as pd
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore


# ----------------------------
# Firebase Connection
# ----------------------------

key_dict = json.loads(st.secrets["firebase_key"])

if not firebase_admin._apps:
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ----------------------------
# Constants
# ----------------------------

#FEE_PER_DAY = 250
MAX_MONTH_FEE = 7100
TODAY = datetime.now().strftime("%Y-%m-%d")

# ----------------------------
# Sidebar Navigation
# ----------------------------

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Add Store",
        "Add Guest",
        "Delete Guest",
        "Mark Attendance",
        "Add Payment",
        "Search Guest"
    ]
)

st.title("🏋 Nutrition Club Management System")

# ----------------------------
# 1️⃣ DASHBOARD
# ----------------------------

if menu == "Dashboard":

    st.header("Club Dashboard")

    guests = db.collection("guests").stream()

    records = []

    for g in guests:

        data = g.to_dict()
        attendance = data.get("attendance", [])

        present_days = sum(1 for a in attendance if a["status"] == "Present")

        fee = MAX_MONTH_FEE

        records.append({
            "Guest Name": data["name"],
            "Store": data["store"],
            "Phone": data["phone"],
            "Days Present": present_days,
            "Total Fee": fee
        })

    df = pd.DataFrame(records)

    st.dataframe(df)

# ----------------------------
# 2️⃣ ADD STORE
# ----------------------------

elif menu == "Add Store":

    st.header("Add Nutrition Club")

    store_name = st.text_input("Store Name")

    if st.button("Add Store"):

        db.collection("stores").document(store_name).set({
            "store": store_name
        })

        st.success("Store Added Successfully")

# ----------------------------
# 3️⃣ ADD GUEST
# ----------------------------

elif menu == "Add Guest":

    st.header("Add Guest")

    stores = db.collection("stores").stream()
    store_list = [s.id for s in stores]

    store = st.selectbox("Select Store", store_list)

    name = st.text_input("Guest Name")
    phone = st.text_input("Phone Number")
    join_date = st.date_input("Date of Joining")

    if st.button("Add Guest"):

        db.collection("guests").document(name).set({

            "name": name,
            "phone": phone,
            "store": store,
            "joining_date": str(join_date),
            "attendance": []

        })

        st.success("Guest Added Successfully")

# ----------------------------
# 4️⃣ DELETE GUEST
# ----------------------------

elif menu == "Delete Guest":

    st.header("Delete Guest")

    guests = db.collection("guests").stream()
    guest_names = [g.id for g in guests]

    selected = st.selectbox("Select Guest", guest_names)

    if st.button("Delete Guest"):

        db.collection("guests").document(selected).delete()

        st.success("Guest Deleted")

# ----------------------------
# 5️⃣ MARK ATTENDANCE
# ----------------------------

elif menu == "Mark Attendance":

    st.header("Mark Attendance")

    guests = db.collection("guests").stream()
    guest_names = [g.id for g in guests]

    guest = st.selectbox("Select Guest", guest_names)

    status = st.radio("Status", ["Present", "Absent"])

    if st.button("Submit Attendance"):

        ref = db.collection("guests").document(guest)
        doc = ref.get().to_dict()

        attendance = doc.get("attendance", [])

        attendance.append({
            "date": TODAY,
            "status": status
        })

        ref.update({"attendance": attendance})

        st.success("Attendance Saved")

# ----------------------------
# 6️⃣ ADD PAYMENT
# ----------------------------

elif menu == "Add Payment":

    st.header("Add Payment")

    guests = db.collection("guests").stream()
    guest_names = [g.id for g in guests]

    guest = st.selectbox("Select Guest", guest_names)

    amount = st.number_input("Amount Paid", min_value=0)

    payment_mode = st.radio(
        "Payment Method",
        ["Cash", "Online"]
    )

    if st.button("Save Payment"):

        db.collection("payments").add({

            "guest": guest,
            "amount": amount,
            "mode": payment_mode,
            "date": str(datetime.now())

        })

        st.success("Payment Recorded")

# ----------------------------
# 7️⃣ SEARCH GUEST
# ----------------------------

elif menu == "Search Guest":

    st.header("Search Guest")

    search_name = st.text_input("Enter Guest Name")

    if st.button("Search"):

        ref = db.collection("guests").document(search_name)
        doc = ref.get()

        if doc.exists:

            data = doc.to_dict()

            st.subheader("Guest Details")

            st.write("Name:", data["name"])
            st.write("Phone:", data["phone"])
            st.write("Store:", data["store"])
            st.write("Joined:", data["joining_date"])

            attendance = data.get("attendance", [])

            df = pd.DataFrame(attendance)

            st.subheader("Attendance")

            st.dataframe(df)

            present_days = sum(
                1 for a in attendance if a["status"] == "Present"
            )

            fee = MAX_MONTH_FEE

            st.subheader("Fee Details")

            st.write("Days Present:", present_days)
            st.write("Total Fee:", fee)

            # Payment History

            st.subheader("Payments")

            payments = db.collection("payments").where(
                "guest", "==", search_name
            ).stream()

            pay_list = []

            for p in payments:

                pay_list.append(p.to_dict())

            if pay_list:

                pay_df = pd.DataFrame(pay_list)

                st.dataframe(pay_df)

            else:

                st.write("No Payments Found")

            # Reminder System

            if present_days >= 15:

                st.error(
                    "⚠ Payment Due Reminder: Guest attended 15+ days but payment may be pending."
                )

        else:


            st.warning("Guest Not Found")




