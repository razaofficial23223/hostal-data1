
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date

DB_PATH = "/kaggle/working/hostel_data.db"

st.set_page_config(
    page_title="Smart Hostel Management",
    page_icon="🏨",
    layout="wide"
)

def get_data(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(query, params)
    conn.commit()
    conn.close()

st.title("🏨 Smart Hostel Management System")
st.caption("Hostel Administration Dashboard")

menu = st.sidebar.selectbox(
    "Select Section",
    ["Dashboard", "Students", "Rooms", "Expenses",
     "Food Management", "Payments"]
)

if menu == "Dashboard":
    st.subheader("Dashboard Overview")

    students = get_data("SELECT * FROM students")
    rooms = get_data("SELECT * FROM rooms")
    expenses = get_data("SELECT * FROM expenses")
    payments = get_data("SELECT * FROM payments")

    total_students = len(students)
    total_rooms = len(rooms)
    available_rooms = len(rooms[rooms["status"] == "Available"]) if total_rooms else 0
    occupied_rooms = len(rooms[rooms["status"] == "Occupied"]) if total_rooms else 0

    income = payments.loc[payments["status"] == "Paid", "amount"].sum() if len(payments) else 0
    total_expenses = expenses["amount"].sum() if len(expenses) else 0

    food_expenses = expenses.loc[
        expenses["category"].str.contains("food", case=False, na=False),
        "amount"
    ].sum() if len(expenses) else 0

    pending = payments.loc[
        payments["status"] == "Pending", "amount"
    ].sum() if len(payments) else 0

    balance = income - total_expenses

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Students", total_students)
    c2.metric("Total Rooms", total_rooms)
    c3.metric("Available Rooms", available_rooms)

    c4, c5, c6 = st.columns(3)
    c4.metric("Occupied Rooms", occupied_rooms)
    c5.metric("Total Income", f"PKR {income:,.0f}")
    c6.metric("Total Expenses", f"PKR {total_expenses:,.0f}")

    c7, c8 = st.columns(2)
    c7.metric("Pending Payments", f"PKR {pending:,.0f}")
    c8.metric("Remaining Balance", f"PKR {balance:,.0f}")

    st.subheader("Recent Payments")
    st.dataframe(
        payments.tail(10).sort_values("id", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Expense Summary")
    if len(expenses):
        summary = expenses.groupby("category")["amount"].sum().reset_index()
        fig = px.pie(summary, names="category", values="amount",
                     title="Expenses by Category")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses added yet.")

elif menu == "Students":
    st.subheader("👨‍🎓 Student Management")

    with st.form("student_form"):
        name = st.text_input("Student Name")
        father = st.text_input("Father Name")
        phone = st.text_input("Phone")
        cnic = st.text_input("CNIC")
        university = st.text_input("University")
        room = st.text_input("Room Number")
        admission = st.date_input("Admission Date", value=date.today())
        rent = st.number_input("Monthly Rent (PKR)", min_value=0.0)
        emergency = st.text_input("Emergency Contact")

        submit = st.form_submit_button("Add Student")

        if submit:
            if name.strip():
                execute("""
                    INSERT INTO students
                    (student_name, father_name, phone, cnic, university,
                     room_number, admission_date, monthly_rent, emergency_contact)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, father, phone, cnic, university, room,
                      str(admission), rent, emergency))
                st.success("Student added successfully!")
                st.rerun()
            else:
                st.error("Student name is required.")

    st.subheader("All Students")
    st.dataframe(get_data("SELECT * FROM students"),
                 use_container_width=True, hide_index=True)

elif menu == "Rooms":
    st.subheader("🚪 Room Management")

    with st.form("room_form"):
        room_no = st.text_input("Room Number")
        capacity = st.number_input("Room Capacity", min_value=1, step=1)
        rent = st.number_input("Monthly Rent (PKR)", min_value=0.0)
        status = st.selectbox("Room Status", ["Available", "Occupied"])
        submit = st.form_submit_button("Add Room")

        if submit:
            try:
                if room_no.strip():
                    execute("""
                        INSERT INTO rooms (room_number, capacity, monthly_rent, status)
                        VALUES (?, ?, ?, ?)
                    """, (room_no, capacity, rent, status))
                    st.success("Room added!")
                    st.rerun()
                else:
                    st.error("Room number is required.")
            except sqlite3.IntegrityError:
                st.error("This room number already exists.")

    st.dataframe(get_data("SELECT * FROM rooms"),
                 use_container_width=True, hide_index=True)

elif menu == "Expenses":
    st.subheader("💰 Expense Management")

    with st.form("expense_form"):
        category = st.selectbox("Category", [
            "Hostel Rent", "Hostel Food", "Electricity",
            "Water", "Transport", "Maintenance", "Other"
        ])
        amount = st.number_input("Amount (PKR)", min_value=0.0)
        description = st.text_input("Description")
        expense_date = st.date_input("Expense Date", value=date.today())
        submit = st.form_submit_button("Add Expense")

        if submit:
            execute("""
                INSERT INTO expenses (category, amount, description, expense_date)
                VALUES (?, ?, ?, ?)
            """, (category, amount, description, str(expense_date)))
            st.success("Expense added!")
            st.rerun()

    st.dataframe(get_data("SELECT * FROM expenses ORDER BY id DESC"),
                 use_container_width=True, hide_index=True)

elif menu == "Food Management":
    st.subheader("🍽️ Food Management")

    with st.form("food_form"):
        food_type = st.selectbox("Food Type", [
            "Breakfast", "Lunch", "Dinner", "Snacks", "Other"
        ])
        amount = st.number_input("Food Expense (PKR)", min_value=0.0)
        description = st.text_input("Description")
        food_date = st.date_input("Date", value=date.today())
        submit = st.form_submit_button("Add Food Record")

        if submit:
            execute("""
                INSERT INTO food_records (food_type, amount, description, food_date)
                VALUES (?, ?, ?, ?)
            """, (food_type, amount, description, str(food_date)))
            st.success("Food record added!")
            st.rerun()

    st.dataframe(get_data("SELECT * FROM food_records ORDER BY id DESC"),
                 use_container_width=True, hide_index=True)

elif menu == "Payments":
    st.subheader("💳 Payment Management")

    students = get_data("SELECT id, student_name FROM students")

    with st.form("payment_form"):
        if len(students):
            selected = st.selectbox(
                "Student",
                students["id"].tolist(),
                format_func=lambda x: students.loc[
                    students["id"] == x, "student_name"
                ].iloc[0]
            )
        else:
            selected = None
            st.warning("Add a student first to link a payment.")

        amount = st.number_input("Amount (PKR)", min_value=0.0)
        payment_date = st.date_input("Payment Date", value=date.today())
        method = st.selectbox("Payment Method", ["Cash", "Bank", "Online"])
        status = st.selectbox("Status", ["Paid", "Pending"])
        description = st.text_input("Description")
        submit = st.form_submit_button("Add Payment")

        if submit:
            if selected is not None:
                student_name = students.loc[
                    students["id"] == selected, "student_name"
                ].iloc[0]

                execute("""
                    INSERT INTO payments
                    (student_id, student_name, amount, payment_date,
                     payment_method, status, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (int(selected), student_name, amount,
                      str(payment_date), method, status, description))
                st.success("Payment added!")
                st.rerun()

    st.subheader("Payment Records")
    st.dataframe(get_data("SELECT * FROM payments ORDER BY id DESC"),
                 use_container_width=True, hide_index=True)

st.sidebar.divider()
st.sidebar.caption("Smart Hostel Management System")
st.sidebar.caption("Developed by Raza Ullah")
