import streamlit as st
import psycopg2.extras
from db import get_connection, init_db

st.set_page_config(page_title="leodropped", page_icon="🧢", layout="centered")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #ffffff; }
[data-testid="stSidebar"] { background-color: #f5f5f5; }
[data-testid="stMetric"] { background: none; border: none; padding: 0; }
[data-testid="stMetricLabel"] { font-size: 0.78rem; color: #888888; font-weight: 400; }
[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 500; color: #111111; }
h1 { color: #111111; font-weight: 600; }
h2, h3 { color: #111111; font-weight: 500; }
hr { border-color: #eeeeee; }
[data-testid="stDataFrame"] { border: 1px solid #eeeeee; border-radius: 4px; }
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

init_db()

st.title("🧢 leodropped")
st.caption("Track every order, hat, and customer — all in one place.")

st.divider()

try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM hats;")
    total_hats = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM customers;")
    total_customers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders;")
    total_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        WHERE o.payment_status = 'Paid';
    """)
    total_revenue = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending';")
    pending_orders = cur.fetchone()[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Hat Products", total_hats)
    col2.metric("Customers", total_customers)
    col3.metric("Total Orders", total_orders)
    col4.metric("Revenue (Paid)", f"${total_revenue:,.2f}")
    col5.metric("Pending Orders", pending_orders)

    st.divider()

    st.subheader("Recent Orders")
    cur.execute("""
        SELECT o.id, c.first_name || ' ' || c.last_name AS customer,
               o.order_date, o.status, o.payment_status,
               COUNT(oi.id) AS items
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id, c.first_name, c.last_name, o.order_date, o.status, o.payment_status
        ORDER BY o.order_date DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()

    if rows:
        import pandas as pd
        df = pd.DataFrame(rows, columns=["Order #", "Customer", "Date", "Status", "Payment", "Items"])
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%b %d, %Y")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No orders yet. Head to Manage Orders to create one!")

    st.divider()

    st.subheader("Orders by Status")
    cur.execute(
