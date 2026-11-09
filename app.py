
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Student Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("expenses.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS categories (
    name TEXT PRIMARY KEY
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()

# Default categories
default_categories = [
    "Hostel Rent",
    "University Transport",
    "Hostel Food",
    "Morning University Food",
    "Evening University Food",
    "Shopping",
    "Personal Expenses",
    "Other"
]

for category in default_categories:
    conn.execute(
        "INSERT OR IGNORE INTO categories (name) VALUES (?)",
        (category,)
    )

conn.execute(
    "INSERT OR IGNORE INTO settings VALUES (?, ?)",
    ("budget", "30000")
)

conn.commit()

# ---------------- FUNCTIONS ----------------

def get_categories():
    return pd.read_sql_query(
        "SELECT name FROM categories ORDER BY name",
        conn
    )["name"].tolist()


def get_budget():
    result = conn.execute(
        "SELECT value FROM settings WHERE key='budget'"
    ).fetchone()

    return float(result[0])


def save_budget(value):
    conn.execute(
        "UPDATE settings SET value=? WHERE key='budget'",
        (str(value),)
    )
    conn.commit()


def load_expenses():
    return pd.read_sql_query(
        "SELECT * FROM expenses ORDER BY date DESC",
        conn
    )


# ---------------- SIDEBAR ----------------

st.sidebar.title("⚙️ Settings")

budget = get_budget()

new_budget = st.sidebar.number_input(
    "Monthly Budget (PKR)",
    min_value=0.0,
    value=budget,
    step=1000.0
)

if st.sidebar.button("Save Budget"):
    save_budget(new_budget)
    st.sidebar.success("Budget saved!")
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("➕ Custom Category")

new_category = st.sidebar.text_input(
    "Enter Category Name"
)

if st.sidebar.button("Add Category"):

    if new_category.strip():

        try:
            conn.execute(
                "INSERT INTO categories (name) VALUES (?)",
                (new_category.strip(),)
            )

            conn.commit()

            st.sidebar.success("Category added!")

        except sqlite3.IntegrityError:
            st.sidebar.warning("Category already exists.")

        st.rerun()

# ---------------- HEADER ----------------

st.title("💰 Student Hostel & University Expense Tracker")

st.write(
    "Manage your monthly budget, expenses, shopping, "
    "hostel rent and university food."
)

# ---------------- ADD EXPENSE ----------------

st.subheader("➕ Add New Expense")

categories = get_categories()

with st.form("expense_form"):

    expense_date = st.date_input(
        "Expense Date",
        value=date.today()
    )

    category = st.selectbox(
        "Expense Category",
        categories
    )

    amount = st.number_input(
        "Amount (PKR)",
        min_value=0.0,
        step=100.0
    )

    description = st.text_input(
        "Description"
    )

    submit = st.form_submit_button(
        "Save Expense"
    )

    if submit:

        if amount > 0:

            conn.execute("""
                INSERT INTO expenses
                (date, category, amount, description)
                VALUES (?, ?, ?, ?)
            """, (
                str(expense_date),
                category,
                amount,
                description
            ))

            conn.commit()

            st.success("Expense saved successfully!")
            st.rerun()

        else:

            st.warning("Enter an amount greater than zero.")

# ---------------- LOAD DATA ----------------

df = load_expenses()

if not df.empty:

    df["date"] = pd.to_datetime(df["date"])

# ---------------- MONTH FILTER ----------------

st.subheader("📅 Monthly Dashboard")

available_months = sorted(
    df["date"].dt.strftime("%Y-%m").unique(),
    reverse=True
) if not df.empty else []

current_month = date.today().strftime("%Y-%m")

if current_month not in available_months:
    available_months.insert(0, current_month)

selected_month = st.selectbox(
    "Select Month",
    available_months
)

if not df.empty:

    monthly_df = df[
        df["date"].dt.strftime("%Y-%m") == selected_month
    ]

else:

    monthly_df = df

# ---------------- DASHBOARD METRICS ----------------

total_expense = (
    monthly_df["amount"].sum()
    if not monthly_df.empty else 0
)

remaining = budget - total_expense

col1, col2, col3 = st.columns(3)

col1.metric(
    "💵 Monthly Budget",
    f"Rs. {budget:,.0f}"
)

col2.metric(
    "💸 Total Expenses",
    f"Rs. {total_expense:,.0f}"
)

col3.metric(
    "💰 Remaining Budget",
    f"Rs. {remaining:,.0f}"
)

# ---------------- PROGRESS BAR ----------------

if budget > 0:

    progress = min(total_expense / budget, 1.0)

    st.progress(progress)

    st.write(
        f"Budget Used: {total_expense / budget * 100:.1f}%"
    )

if remaining < 0:

    st.error(
        f"⚠️ Budget exceeded by Rs. {abs(remaining):,.0f}!"
    )

# ---------------- CATEGORY CHART ----------------

st.subheader("📊 Category-wise Expenses")

if not monthly_df.empty:

    category_total = (
        monthly_df.groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    fig = px.pie(
        category_total,
        names="category",
        values="amount",
        title="Expense Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    bar_chart = px.bar(
        category_total,
        x="category",
        y="amount",
        title="Category Expense Comparison"
    )

    st.plotly_chart(
        bar_chart,
        use_container_width=True
    )

# ---------------- DAILY EXPENSES ----------------

st.subheader("📆 Daily Expenses")

if not monthly_df.empty:

    daily_total = (
        monthly_df.groupby("date")["amount"]
        .sum()
        .reset_index()
    )

    daily_chart = px.line(
        daily_total,
        x="date",
        y="amount",
        title="Daily Expense Trend",
        markers=True
    )

    st.plotly_chart(
        daily_chart,
        use_container_width=True
    )

# ---------------- EXPENSE HISTORY ----------------

st.subheader("📋 Expense History")

if not monthly_df.empty:

    st.dataframe(
        monthly_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No expenses available for this month.")

# ---------------- EDIT EXPENSE ----------------

st.subheader("✏️ Edit Expense")

if not df.empty:

    expense_id = st.selectbox(
        "Select Expense ID",
        df["id"].tolist()
    )

    selected = df[df["id"] == expense_id].iloc[0]

    edit_categories = get_categories()

    with st.form("edit_form"):

        edit_category = st.selectbox(
            "Category",
            edit_categories,
            index=(
                edit_categories.index(selected["category"])
                if selected["category"] in edit_categories
                else 0
            )
        )

        edit_amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=float(selected["amount"])
        )

        edit_description = st.text_input(
            "Description",
            value=str(selected["description"])
        )

        update = st.form_submit_button(
            "Update Expense"
        )

        if update:

            conn.execute("""
                UPDATE expenses
                SET category=?, amount=?, description=?
                WHERE id=?
            """, (
                edit_category,
                edit_amount,
                edit_description,
                expense_id
            ))

            conn.commit()

            st.success("Expense updated!")
            st.rerun()

# ---------------- DELETE EXPENSE ----------------

st.subheader("🗑️ Delete Expense")

if not df.empty:

    delete_id = st.selectbox(
        "Select Expense to Delete",
        df["id"].tolist(),
        key="delete_expense"
    )

    if st.button("Delete Selected Expense"):

        conn.execute(
            "DELETE FROM expenses WHERE id=?",
            (delete_id,)
        )

        conn.commit()

        st.success("Expense deleted!")
        st.rerun()

# ---------------- CSV DOWNLOAD ----------------

st.subheader("📥 Download Expenses")

if not df.empty:

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Expense Report (CSV)",
        data=csv,
        file_name="student_expenses.csv",
        mime="text/csv"
    )

st.markdown("---")

st.caption(
    "Student Expense Tracker | Python + Streamlit + SQLite"
)
