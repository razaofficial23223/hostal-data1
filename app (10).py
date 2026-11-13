
import os
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ---------------- DATABASE ----------------

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "hostel_data.db"
)

st.set_page_config(
    page_title="Smart Hostel Management",
    page_icon="🏨",
    layout="wide"
)

def get_connection():
    return sqlite3.connect(DB_PATH)

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        father_name TEXT,
        phone TEXT,
        cnic TEXT,
        university TEXT,
        room_number TEXT,
        admission_date TEXT,
        monthly_rent REAL,
        emergency_contact TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE,
        capacity INTEGER,
        monthly_rent REAL,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        amount REAL,
        description TEXT,
        expense_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        student_name TEXT,
        amount REAL,
        payment_date TEXT,
        payment_method TEXT,
        status TEXT,
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_type TEXT,
        amount REAL,
        description TEXT,
        food_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT UNIQUE,
        budget_amount REAL
    )
    """)

    conn.commit()
    conn.close()

initialize_database()

# ---------------- DATABASE FUNCTIONS ----------------

def get_data(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def money(value):
    return f"PKR {value:,.0f}"

# ---------------- EXPENSE CATEGORIES ----------------

EXPENSE_CATEGORIES = [
    "Hostel Rent",
    "Hostel Food",
    "University Transport",
    "Morning University Food",
    "Evening University Food",
    "Personal Expenses",
    "Shopping",
    "Electricity",
    "Water",
    "Maintenance",
    "Other"
]

# ---------------- SIDEBAR ----------------

st.sidebar.title("🏨 Hostel Management")

menu = st.sidebar.selectbox(
    "Select Section",
    [
        "Dashboard",
        "Students",
        "Rooms",
        "Expenses",
        "Food Management",
        "Payments"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Developed by Raza Ullah")

# ---------------- HEADER ----------------

st.title("🏨 Smart Hostel Management System")
st.caption("Professional Hostel Administration Dashboard")

# ---------------- DASHBOARD ----------------

if menu == "Dashboard":

    st.subheader("📊 Dashboard Overview")

    students = get_data("SELECT * FROM students")
    rooms = get_data("SELECT * FROM rooms")
    expenses = get_data("SELECT * FROM expenses")
    payments = get_data("SELECT * FROM payments")

    total_students = len(students)
    total_rooms = len(rooms)

    available_rooms = (
        len(rooms[rooms["status"] == "Available"])
        if total_rooms else 0
    )

    occupied_rooms = (
        len(rooms[rooms["status"] == "Occupied"])
        if total_rooms else 0
    )

    income = (
        payments.loc[
            payments["status"] == "Paid", "amount"
        ].sum()
        if len(payments) else 0
    )

    total_expenses = (
        expenses["amount"].sum()
        if len(expenses) else 0
    )

    pending = (
        payments.loc[
            payments["status"] == "Pending", "amount"
        ].sum()
        if len(payments) else 0
    )

    balance = income - total_expenses

    # Dashboard cards

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Students", total_students)
    c2.metric("Total Rooms", total_rooms)
    c3.metric("Available Rooms", available_rooms)

    c4, c5, c6 = st.columns(3)

    c4.metric("Occupied Rooms", occupied_rooms)
    c5.metric("Total Income", money(income))
    c6.metric("Total Expenses", money(total_expenses))

    c7, c8 = st.columns(2)

    c7.metric("Pending Payments", money(pending))
    c8.metric("Remaining Balance", money(balance))

    # Recent Payments

    st.subheader("💳 Recent Payments")

    if len(payments):
        recent_payments = payments.sort_values(
            "id", ascending=False
        ).head(10)

        st.dataframe(
            recent_payments,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No payments available.")

    # Expense Chart

    st.subheader("📈 Expense Summary")

    if len(expenses):
        summary = (
            expenses.groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.pie(
            summary,
            names="category",
            values="amount",
            title="Expenses by Category",
            hole=0.4
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses added yet.")

# ---------------- STUDENTS ----------------

elif menu == "Students":

    st.subheader("👨‍🎓 Student Management")

    with st.form("student_form"):

        name = st.text_input("Student Name")
        father = st.text_input("Father Name")
        phone = st.text_input("Phone")
        cnic = st.text_input("CNIC")
        university = st.text_input("University")
        room = st.text_input("Room Number")

        admission = st.date_input(
            "Admission Date",
            value=date.today()
        )

        rent = st.number_input(
            "Monthly Rent (PKR)",
            min_value=0.0
        )

        emergency = st.text_input("Emergency Contact")

        submit = st.form_submit_button("Add Student")

        if submit:

            if not name.strip():
                st.error("Student name is required.")

            else:
                execute("""
                    INSERT INTO students
                    (
                        student_name, father_name, phone,
                        cnic, university, room_number,
                        admission_date, monthly_rent,
                        emergency_contact
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, father, phone, cnic,
                    university, room, str(admission),
                    rent, emergency
                ))

                st.success("Student added successfully!")
                st.rerun()

    st.subheader("All Students")

    students = get_data("SELECT * FROM students ORDER BY id DESC")

    st.dataframe(
        students,
        use_container_width=True,
        hide_index=True
    )

# ---------------- ROOMS ----------------

elif menu == "Rooms":

    st.subheader("🚪 Room Management")

    with st.form("room_form"):

        room_no = st.text_input("Room Number")

        capacity = st.number_input(
            "Room Capacity",
            min_value=1,
            step=1
        )

        rent = st.number_input(
            "Monthly Rent (PKR)",
            min_value=0.0
        )

        status = st.selectbox(
            "Room Status",
            ["Available", "Occupied"]
        )

        submit = st.form_submit_button("Add Room")

        if submit:

            if not room_no.strip():
                st.error("Room number is required.")

            else:
                try:
                    execute("""
                        INSERT INTO rooms
                        (room_number, capacity, monthly_rent, status)
                        VALUES (?, ?, ?, ?)
                    """, (room_no, capacity, rent, status))

                    st.success("Room added successfully!")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error("This room already exists.")

    st.subheader("All Rooms")

    st.dataframe(
        get_data("SELECT * FROM rooms ORDER BY id DESC"),
        use_container_width=True,
        hide_index=True
    )

# ---------------- EXPENSES ----------------

elif menu == "Expenses":

    st.subheader("💰 Expense Management")

    with st.form("expense_form"):

        category = st.selectbox(
            "Expense Category",
            EXPENSE_CATEGORIES
        )

        amount = st.number_input(
            "Amount (PKR)",
            min_value=0.0,
            step=100.0
        )

        description = st.text_input(
            "Description",
            placeholder="Enter expense details"
        )

        expense_date = st.date_input(
            "Expense Date",
            value=date.today()
        )

        submit = st.form_submit_button("Add Expense")

        if submit:

            if amount <= 0:
                st.error("Enter an amount greater than zero.")

            else:
                conn = get_connection()

                duplicate = conn.execute("""
                    SELECT id FROM expenses
                    WHERE category = ?
                    AND amount = ?
                    AND description = ?
                    AND expense_date = ?
                """, (
                    category,
                    amount,
                    description.strip(),
                    str(expense_date)
                )).fetchone()

                conn.close()

                if duplicate:
                    st.warning(
                        "This exact expense already exists. "
                        "Please check before adding again."
                    )

                else:
                    execute("""
                        INSERT INTO expenses
                        (category, amount, description, expense_date)
                        VALUES (?, ?, ?, ?)
                    """, (
                        category,
                        amount,
                        description.strip(),
                        str(expense_date)
                    ))

                    st.success("Expense added successfully!")
                    st.rerun()

    # Expense History

    st.subheader("📋 Expense History")

    expenses = get_data(
        "SELECT * FROM expenses ORDER BY id DESC"
    )

    if len(expenses):

        # Hide exact duplicate rows in display only.
        expenses = expenses.drop_duplicates(
            subset=[
                "expense_date",
                "category",
                "amount",
                "description"
            ],
            keep="first"
        )

        display_expenses = expenses.rename(
            columns={
                "expense_date": "Date",
                "category": "Category",
                "amount": "Amount",
                "description": "Description"
            }
        )

        st.dataframe(
            display_expenses[
                ["Date", "Category", "Amount", "Description"]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Expenses",
            money(expenses["amount"].sum())
        )

    else:
        st.info("No expenses added yet.")

# ---------------- FOOD MANAGEMENT ----------------

elif menu == "Food Management":

    st.subheader("🍽️ Food Management")

    with st.form("food_form"):

        food_type = st.selectbox(
            "Food Type",
            ["Breakfast", "Lunch", "Dinner", "Snacks", "Other"]
        )

        amount = st.number_input(
            "Food Expense (PKR)",
            min_value=0.0
        )

        description = st.text_input("Description")

        food_date = st.date_input(
            "Food Date",
            value=date.today()
        )

        submit = st.form_submit_button("Add Food Record")

        if submit:

            if amount <= 0:
                st.error("Enter a valid amount.")

            else:
                execute("""
                    INSERT INTO food_records
                    (food_type, amount, description, food_date)
                    VALUES (?, ?, ?, ?)
                """, (
                    food_type,
                    amount,
                    description,
                    str(food_date)
                ))

                st.success("Food record added!")
                st.rerun()

    food_records = get_data(
        "SELECT * FROM food_records ORDER BY id DESC"
    )

    st.subheader("Food History")

    st.dataframe(
        food_records,
        use_container_width=True,
        hide_index=True
    )

    food_total = (
        food_records["amount"].sum()
        if len(food_records) else 0
    )

    st.metric("Food Records Total", money(food_total))

    st.caption(
        "Food Management records are separate from Expenses. "
        "Do not enter the same food expense in both sections."
    )

# ---------------- PAYMENTS ----------------

elif menu == "Payments":

    st.subheader("💳 Payment Management")

    students = get_data(
        "SELECT id, student_name FROM students"
    )

    with st.form("payment_form"):

        if len(students):

            selected = st.selectbox(
                "Select Student",
                students["id"].tolist(),
                format_func=lambda x: students.loc[
                    students["id"] == x,
                    "student_name"
                ].iloc[0]
            )

        else:
            selected = None
            st.warning("Please add a student first.")

        amount = st.number_input(
            "Payment Amount (PKR)",
            min_value=0.0
        )

        payment_date = st.date_input(
            "Payment Date",
            value=date.today()
        )

        method = st.selectbox(
            "Payment Method",
            ["Cash", "Bank", "Online"]
        )

        status = st.selectbox(
            "Payment Status",
            ["Paid", "Pending"]
        )

        description = st.text_input("Description")

        submit = st.form_submit_button("Add Payment")

        if submit:

            if selected is None:
                st.error("Add a student before recording payment.")

            elif amount <= 0:
                st.error("Enter a valid payment amount.")

            else:

                student_name = students.loc[
                    students["id"] == selected,
                    "student_name"
                ].iloc[0]

                execute("""
                    INSERT INTO payments
                    (
                        student_id, student_name, amount,
                        payment_date, payment_method,
                        status, description
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(selected),
                    student_name,
                    amount,
                    str(payment_date),
                    method,
                    status,
                    description
                ))

                st.success("Payment added successfully!")
                st.rerun()

    st.subheader("Payment Records")

    payments = get_data(
        "SELECT * FROM payments ORDER BY id DESC"
    )

    st.dataframe(
        payments,
        use_container_width=True,
        hide_index=True
    )

    paid_total = (
        payments.loc[
            payments["status"] == "Paid", "amount"
        ].sum()
        if len(payments) else 0
    )

    pending_total = (
        payments.loc[
            payments["status"] == "Pending", "amount"
        ].sum()
        if len(payments) else 0
    )

    p1, p2 = st.columns(2)

    p1.metric("Paid Amount", money(paid_total))
    p2.metric("Pending Amount", money(pending_total))

