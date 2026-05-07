import streamlit as st
from db import get_connection, get_order_statuses, get_payment_statuses

st.set_page_config(page_title="Orders | leodropped", page_icon="🧢", layout="wide")
st.title("📦 Manage Orders")

# Dynamic dropdowns — pulled from order_statuses and payment_statuses tables
ORDER_STATUSES = get_order_statuses()
PAYMENT_STATUSES = get_payment_statuses()

def load_customers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, first_name || ' ' || last_name FROM customers ORDER BY last_name, first_name;")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {name: cid for cid, name in rows}

def load_hats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, style || ' - ' || color || ' (' || size || ') $' || price::text FROM hats WHERE quantity_in_stock > 0 ORDER BY style;")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {label: hid for hid, label in rows}

# ── Create New Order ──────────────────────────────────────────────────────────
with st.expander("➕ Create New Order", expanded=False):
    customers = load_customers()
    hats = load_hats()

    if not customers:
        st.warning("Add at least one customer before creating an order.")
    elif not hats:
        st.warning("Add at least one hat with stock before creating an order.")
    else:
        with st.form("create_order"):
            selected_customer = st.selectbox("Customer *", list(customers.keys()))
            c1, c2 = st.columns(2)
            status = c1.selectbox("Order Status *", ORDER_STATUSES)
            payment_status = c2.selectbox("Payment Status *", PAYMENT_STATUSES)
            notes = st.text_area("Notes (optional)")

            st.markdown("**Add Items to Order**")
            selected_hat = st.selectbox("Hat *", list(hats.keys()))
            quantity = st.number_input("Quantity *", min_value=1, step=1, value=1)

            submitted = st.form_submit_button("Create Order")
            if submitted:
                if not selected_customer or not selected_hat:
                    st.error("Please select a customer and at least one hat.")
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        customer_id = customers[selected_customer]
                        hat_id = hats[selected_hat]

                        # Get hat price
                        cur.execute("SELECT price, quantity_in_stock FROM hats WHERE id=%s;", (hat_id,))
                        hat_info = cur.fetchone()
                        unit_price = hat_info[0]
                        stock = hat_info[1]

                        if quantity > stock:
                            st.error(f"Not enough stock. Only {stock} available.")
                        else:
                            # Create order
                            cur.execute(
                                "INSERT INTO orders (customer_id, status, payment_status, notes) VALUES (%s, %s, %s, %s) RETURNING id;",
                                (customer_id, status, payment_status, notes.strip() or None)
                            )
                            order_id = cur.fetchone()[0]

                            # Create order item
                            cur.execute(
                                "INSERT INTO order_items (order_id, hat_id, quantity, unit_price) VALUES (%s, %s, %s, %s);",
                                (order_id, hat_id, quantity, unit_price)
                            )

                            # Deduct stock
                            cur.execute(
                                "UPDATE hats SET quantity_in_stock = quantity_in_stock - %s WHERE id=%s;",
                                (quantity, hat_id)
                            )

                            conn.commit(); cur.close(); conn.close()
                            st.success(f"Order #{order_id} created for {selected_customer}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating order: {e}")

# ── Filter Orders ─────────────────────────────────────────────────────────────
st.subheader("All Orders")
filter_status = st.selectbox("Filter by status", ["All"] + ORDER_STATUSES)

# ── Load Orders ───────────────────────────────────────────────────────────────
try:
    conn = get_connection()
    cur = conn.cursor()
    if filter_status != "All":
        cur.execute("""
            SELECT o.id, c.first_name || ' ' || c.last_name, o.order_date,
                   o.status, o.payment_status,
                   COUNT(oi.id) as items,
                   COALESCE(SUM(oi.quantity * oi.unit_price), 0) as total
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.status = %s
            GROUP BY o.id, c.first_name, c.last_name, o.order_date, o.status, o.payment_status
            ORDER BY o.order_date DESC;
        """, (filter_status,))
    else:
        cur.execute("""
            SELECT o.id, c.first_name || ' ' || c.last_name, o.order_date,
                   o.status, o.payment_status,
                   COUNT(oi.id) as items,
                   COALESCE(SUM(oi.quantity * oi.unit_price), 0) as total
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.id, c.first_name, c.last_name, o.order_date, o.status, o.payment_status
            ORDER BY o.order_date DESC;
        """)
    orders = cur.fetchall()
    cur.close(); conn.close()
except Exception as e:
    st.error(f"Database error: {e}")
    orders = []

if not orders:
    st.info("No orders found.")
else:
    h0, h1, h2, h3, h4, h5, h6, hv, he, hd = st.columns([1, 2.5, 2, 1.5, 1.5, 1, 1.5, 1, 1, 1])
    h0.markdown("**#**"); h1.markdown("**Customer**"); h2.markdown("**Date**")
    h3.markdown("**Status**"); h4.markdown("**Payment**"); h5.markdown("**Items**")
    h6.markdown("**Total**"); hv.markdown("**View**"); he.markdown("**Edit**"); hd.markdown("**Delete**")
    st.divider()

    for order in orders:
        oid, cname, odate, ostatus, opay, items, total = order
        c0, c1, c2, c3, c4, c5, c6, cv, ce, cd = st.columns([1, 2.5, 2, 1.5, 1.5, 1, 1.5, 1, 1, 1])
        c0.write(oid); c1.write(cname)
        c2.write(odate.strftime("%b %d, %Y") if odate else "—")
        c3.write(ostatus); c4.write(opay); c5.write(items); c6.write(f"${total:.2f}")

        if cv.button("👁️", key=f"view_{oid}"):
            st.session_state["view_order"] = oid
        if ce.button("✏️", key=f"edit_{oid}"):
            st.session_state["editing_order"] = oid
        if cd.button("🗑️", key=f"del_{oid}"):
            st.session_state["confirm_del_order"] = oid

    # ── View Order Detail ──────────────────────────────────────────────────────
    view_id = st.session_state.get("view_order")
    if view_id:
        st.divider()
        st.subheader(f"Order #{view_id} Detail")
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT oi.id, h.style, h.color, h.size, oi.quantity, oi.unit_price,
                       (oi.quantity * oi.unit_price) as subtotal
                FROM order_items oi
                JOIN hats h ON h.id = oi.hat_id
                WHERE oi.order_id = %s;
            """, (view_id,))
            items = cur.fetchall()
            cur.execute("SELECT notes FROM orders WHERE id=%s;", (view_id,))
            notes_row = cur.fetchone()
            cur.close(); conn.close()

            if items:
                import pandas as pd
                df = pd.DataFrame(items, columns=["Item #", "Style", "Color", "Size", "Qty", "Unit Price", "Subtotal"])
                df["Unit Price"] = df["Unit Price"].apply(lambda x: f"${x:.2f}")
                df["Subtotal"] = df["Subtotal"].apply(lambda x: f"${x:.2f}")
                st.dataframe(df, use_container_width=True, hide_index=True)
                total_val = sum(r[6] for r in items)
                st.markdown(f"**Order Total: ${total_val:.2f}**")
            else:
                st.info("No items in this order.")

            if notes_row and notes_row[0]:
                st.markdown(f"**Notes:** {notes_row[0]}")

        except Exception as e:
            st.error(f"Error loading order detail: {e}")

        if st.button("Close", key="close_view"):
            del st.session_state["view_order"]; st.rerun()

    # ── Edit Order ─────────────────────────────────────────────────────────────
    edit_id = st.session_state.get("editing_order")
    if edit_id:
        order_data = next((o for o in orders if o[0] == edit_id), None)
        if order_data:
            st.divider()
            st.subheader(f"Edit Order #{edit_id}")
            with st.form("edit_order"):
                c1, c2 = st.columns(2)
                new_status = c1.selectbox("Status *", ORDER_STATUSES, index=ORDER_STATUSES.index(order_data[3]))
                new_payment = c2.selectbox("Payment Status *", PAYMENT_STATUSES, index=PAYMENT_STATUSES.index(order_data[4]))
                new_notes = st.text_area("Notes")
                save = st.form_submit_button("💾 Save Changes")
                cancel = st.form_submit_button("Cancel")

                if save:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE orders SET status=%s, payment_status=%s, notes=%s WHERE id=%s;",
                            (new_status, new_payment, new_notes.strip() or None, edit_id)
                        )
                        conn.commit(); cur.close(); conn.close()
                        del st.session_state["editing_order"]
                        st.success("Order updated!"); st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                if cancel:
                    del st.session_state["editing_order"]; st.rerun()

    # ── Delete Confirmation ────────────────────────────────────────────────────
    confirm_id = st.session_state.get("confirm_del_order")
    if confirm_id:
        order_data = next((o for o in orders if o[0] == confirm_id), None)
        if order_data:
            st.divider()
            st.warning(f"⚠️ Delete Order #{confirm_id} for **{order_data[1]}**? This will also remove all order items.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes, Delete", key="yes_del_o"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM orders WHERE id=%s;", (confirm_id,))
                    conn.commit(); cur.close(); conn.close()
                    del st.session_state["confirm_del_order"]
                    st.success("Order deleted."); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            if c2.button("❌ Cancel", key="no_del_o"):
                del st.session_state["confirm_del_order"]; st.rerun()
