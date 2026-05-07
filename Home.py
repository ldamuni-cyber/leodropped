import streamlit as st
from db import get_connection, init_db

st.set_page_config(page_title="leodropped", page_icon="🧢", layout="centered")

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

    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending';")
    pending_orders = cur.fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Hat Products", total_hats)
    col2.metric("Customers", total_customers)
    col3.metric("Total Orders", total_orders)
    col4.metric("Pending Orders", pending_orders)

    st.divider()
    st.subheader("Recent Orders")

    cur.execute("SELECT o.id, o.order_date, o.status, o.payment_status FROM orders o ORDER BY o.order_date DESC LIMIT 10;")
    rows = cur.fetchall()

    if rows:
        import pandas as pd
        df = pd.DataFrame(rows, columns=["Order #", "Date", "Status", "Payment"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No orders yet!")

    cur.close()
    conn.close()

except Exception as e:
    st.error(f"Database error: {e}")
