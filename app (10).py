
import os
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ================= DATABASE =================

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "hostel_data.db"
)

st.set_page_config(
    page_title="Smart Hostel Management",
    page_icon="🏨",
    layout="wide"
)

def connect():
    return sqlite3.connect(DB_PATH)

def initialize_database():
    conn = connect()
    c = conn.cursor()

    c.execute("""
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
        emergency_contact TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE,
        capacity INTEGER,
        monthly_rent REAL,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        amount REAL,
        description TEXT,
        expense_date TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS food_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_type TEXT,
        amount REAL,
        description TEXT,
        food_date TEXT
    )
    """)

    c.execute("""
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

    conn.commit()
    conn.close()

initialize_database()

def read_data(table):
    conn = connect()
    df = pd.read_sql_query(
        f"SELECT * FROM {table} ORDER BY id DESC",
        conn
    )
    conn.close()
    return df

def insert_data(table, columns, values):
    conn = connect()
    placeholders = ", ".join(["?"] * len(values))
    column_names = ", ".join(columns)

    conn.execute(
        f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})",
        values
    )
    conn.commit()
    conn.close()

def update_data(table, record_id, columns, values):
    conn = connect()
    assignments = ", ".join([f"{col}=?" for col in columns])

    conn.execute(
        f"UPDATE {table} SET {assignments} WHERE id=?",
        tuple(values) + (record_id,)
    )
    conn.commit()
    conn.close()

def delete_data(table, record_id):
    conn = connect()
    conn.execute(
        f"DELETE FROM {table} WHERE id=?",
        (record_id,)
    )
    conn.commit()
    conn.close()

def money(value):
    return f"PKR {value:,.0f}"

def manage_records(table, label):
    df = read_data(table)

    st.subheader(f"Manage {label}")

    if df.empty:
        st.info(f"No {label} records available.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        f"Select {label} Record ID to Edit or Delete",
        df["id"].tolist(),
        key=f"{table}_selected"
    )

    record = df[df["id"] == selected_id].iloc[0]

    with st.form(f"{table}_edit_form"):
        st.write(f"Editing Record #{selected_id}")

        new_values = {}

        for col in df.columns:
            if col == "id":
                continue

            value = record[col]

            if col in ["amount", "monthly_rent"]:
                new_values[col] = st.number_input(
                    col.replace("_", " ").title(),
                    min_value=0.0,
                    value=float(value) if pd.notna(value) else 0.0,
                    key=f"{table}_{col}"
                )

            elif col == "capacity":
                new_values[col] = st.number_input(
                    "Capacity",
                    min_value=1,
                    value=int(value) if pd.notna(value) else 1,
                    key=f"{table}_{col}"
                )

            else:
                new_values[col] = st.text_input(
                    col.replace("_", " ").title(),
                    value="" if pd.isna(value) else str(value),
                    key=f"{table}_{col}"
                )

        update_button = st.form_submit_button("💾 Update Record")

        if update_button:
            update_data(
                table,
                int(selected_id),
                list(new_values.keys()),
                list(new_values.values())
            )
            st.success("Record updated successfully!")
            st.rerun()

    st.divider()

    confirm_delete = st.checkbox(
        f"Confirm deletion of {label} record #{selected_id}",
        key=f"{table}_confirm_delete"
    )

    if st.button(
        f"🗑️ Delete Selected {label} Record",
        key=f"{table}_delete"
    ):
        if confirm_delete:
            delete_data(table, int(selected_id))
            st.success("Record deleted successfully!")
            st.rerun()
        else:
            st.warning("Please confirm deletion first.")

# ================= SIDEBAR =================

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

st.title("🏨 Smart Hostel Management System")
st.caption("Professional Hostel Administration Dashboard")

# ================= DASHBOARD =================

if menu == "Dashboard":

    students = read_data("students")
    rooms = read_data("rooms")
    expenses = read_data("expenses")
    payments = read_data("payments")
    food = read_data("food_records")

    income = (
        payments.loc[payments["status"] == "Paid", "amount"].sum()
        if len(payments) else 0
    )

    total_expenses = (
        expenses["amount"].sum() if len(expenses) else 0
    )

    pending = (
        payments.loc[payments["status"] == "Pending", "amount"].sum()
        if len(payments) else 0
    )

    available = (
        len(rooms[rooms["status"] == "Available"])
        if len(rooms) else 0
    )

    occupied = (
        len(rooms[rooms["status"] == "Occupied"])
        if len(rooms) else 0
    )

    st.subheader("📊 Dashboard Overview")

    a, b, c = st.columns(3)
    a.metric("Total Students", len(students))
    b.metric("Total Rooms", len(rooms))
    c.metric("Available Rooms", available)

    a, b, c = st.columns(3)
    a.metric("Occupied Rooms", occupied)
    b.metric("Total Income", money(income))
    c.metric("Total Expenses", money(total_expenses))

    a, b = st.columns(2)
    a.metric("Pending Payments", money(pending))
    b.metric("Remaining Balance", money(income - total_expenses))

    st.subheader("💳 Recent Payments")

    if len(payments):
        st.dataframe(
            payments.head(10),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No payments available.")

    st.subheader("📈 Expense Summary")

    if len(expenses):
        summary = expenses.groupby(
            "category", as_index=False
        )["amount"].sum()

        fig = px.pie(
            summary,
            names="category",
            values="amount",
            hole=0.4,
            title="Expenses by Category"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.metric(
        "Food Records Total",
        money(food["amount"].sum() if len(food) else 0)
    )

# ================= STUDENTS =================

elif menu == "Students":

    st.subheader("👨‍🎓 Student Management")

    with st.form("add_student"):
        name = st.text_input("Student Name")
        father = st.text_input("Father Name")
        phone = st.text_input("Phone")
        cnic = st.text_input("CNIC")
        university = st.text_input("University")
        room = st.text_input("Room Number")
        admission = st.date_input("Admission Date")
        rent = st.number_input("Monthly Rent", min_value=0.0)
        emergency = st.text_input("Emergency Contact")

        submit = st.form_submit_button("➕ Add Student")

        if submit:
            if name.strip():
                insert_data(
                    "students",
                    [
                        "student_name", "father_name", "phone",
                        "cnic", "university", "room_number",
                        "admission_date", "monthly_rent",
                        "emergency_contact"
                    ],
                    [
                        name, father, phone, cnic, university,
                        room, str(admission), rent, emergency
                    ]
                )
                st.success("Student added!")
                st.rerun()
            else:
                st.error("Student name is required.")

    manage_records("students", "Students")

# ================= ROOMS =================

elif menu == "Rooms":

    st.subheader("🚪 Room Management")

    with st.form("add_room"):
        room_no = st.text_input("Room Number")
        capacity = st.number_input("Room Capacity", min_value=1)
        rent = st.number_input("Monthly Rent", min_value=0.0)
        status = st.selectbox(
            "Status", ["Available", "Occupied"]
        )

        submit = st.form_submit_button("➕ Add Room")

        if submit:
            try:
                if room_no.strip():
                    insert_data(
                        "rooms",
                        ["room_number", "capacity", "monthly_rent", "status"],
                        [room_no, capacity, rent, status]
                    )
                    st.success("Room added!")
                    st.rerun()
                else:
                    st.error("Room number is required.")
            except sqlite3.IntegrityError:
                st.error("Room already exists.")

    manage_records("rooms", "Rooms")

# ================= EXPENSES =================

elif menu == "Expenses":

    st.subheader("💰 Expense Management")

    categories = [
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

    with st.form("add_expense"):
        category = st.selectbox("Expense Category", categories)
        amount = st.number_input("Amount (PKR)", min_value=0.0)
        description = st.text_input("Description")
        expense_date = st.date_input("Expense Date")

        submit = st.form_submit_button("➕ Add Expense")

        if submit:
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                conn = connect()

                duplicate = conn.execute("""
                    SELECT id FROM expenses
                    WHERE category=?
                    AND amount=?
                    AND description=?
                    AND expense_date=?
                """, (
                    category, amount, description.strip(),
                    str(expense_date)
                )).fetchone()

                conn.close()

                if duplicate:
                    st.warning(
                        "This exact expense already exists. "
                        "Check the history before adding it again."
                    )
                else:
                    insert_data(
                        "expenses",
                        ["category", "amount", "description", "expense_date"],
                        [category, amount, description.strip(), str(expense_date)]
                    )
                    st.success("Expense added!")
                    st.rerun()

    st.subheader("📋 Expense History")

    expenses = read_data("expenses")

    if len(expenses):
        visible = expenses.drop_duplicates(
            subset=["expense_date", "category", "amount", "description"],
            keep="first"
        )

        st.dataframe(
            visible[[
                "id", "expense_date", "category",
                "amount", "description"
            ]],
            use_container_width=True,
            hide_index=True
        )

        st.metric("Total Expenses", money(expenses["amount"].sum()))

        st.divider()
        st.subheader("🧹 Remove Exact Duplicate Expenses")

        st.caption(
            "This will permanently delete repeated records "
            "with the same date, category, amount and description. "
            "One copy will be kept."
        )

        confirm_cleanup = st.checkbox(
            "I confirm that I want to remove exact duplicate expenses."
        )

        if st.button("Remove Duplicate Expenses"):
            if confirm_cleanup:
                conn = connect()
                conn.execute("""
                    DELETE FROM expenses
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM expenses
                        GROUP BY expense_date, category, amount, description
                    )
                """)
                conn.commit()
                conn.close()

                st.success("Duplicate expenses removed!")
                st.rerun()
            else:
                st.warning("Please confirm first.")

    manage_records("expenses", "Expenses")

# ================= FOOD =================

elif menu == "Food Management":

    st.subheader("🍽️ Food Management")

    with st.form("add_food"):
        food_type = st.selectbox(
            "Food Type",
            ["Breakfast", "Lunch", "Dinner", "Snacks", "Other"]
        )

        amount = st.number_input("Amount (PKR)", min_value=0.0)
        description = st.text_input("Description")
        food_date = st.date_input("Food Date")

        submit = st.form_submit_button("➕ Add Food Record")

        if submit:
            if amount > 0:
                insert_data(
                    "food_records",
                    ["food_type", "amount", "description", "food_date"],
                    [food_type, amount, description, str(food_date)]
                )
                st.success("Food record added!")
                st.rerun()
            else:
                st.error("Enter a valid amount.")

    manage_records("food_records", "Food Records")

# ================= PAYMENTS =================

elif menu == "Payments":

    st.subheader("💳 Payment Management")

    students = read_data("students")

    with st.form("add_payment"):

        if len(students):
            selected = st.selectbox(
                "Select Student",
                students["id"].tolist(),
                format_func=lambda x: students.loc[
                    students["id"] == x, "student_name"
                ].iloc[0]
            )
        else:
            selected = None
            st.warning("Add a student first.")

        amount = st.number_input("Amount (PKR)", min_value=0.0)
        payment_date = st.date_input("Payment Date")
        method = st.selectbox(
            "Payment Method", ["Cash", "Bank", "Online"]
        )
        status = st.selectbox(
            "Payment Status", ["Paid", "Pending"]
        )
        description = st.text_input("Description")

        submit = st.form_submit_button("➕ Add Payment")

        if submit:
            if selected is not None and amount > 0:
                student_name = students.loc[
                    students["id"] == selected,
                    "student_name"
                ].iloc[0]

                insert_data(
                    "payments",
                    [
                        "student_id", "student_name", "amount",
                        "payment_date", "payment_method",
                        "status", "description"
                    ],
                    [
                        int(selected), student_name, amount,
                        str(payment_date), method, status, description
                    ]
                )

                st.success("Payment added!")
                st.rerun()
            else:
                st.error("Select a student and enter a valid amount.")

    manage_records("payments", "Payments")

# ================= FOOTER =================

st.sidebar.divider()
st.sidebar.caption("Smart Hostel Management System")
st.sidebar.caption("Developed by Raza Ullah")
