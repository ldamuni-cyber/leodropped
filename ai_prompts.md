import streamlit as st
import re
from db import get_connection, get_sizes

st.set_page_config(page_title="Inventory | leodropped", page_icon="🧢", layout="wide")
st.title("🧢 Manage Inventory")

# Dynamic dropdown — pulled from hat_sizes table in the database
SIZES = get_sizes()

# ── Add Hat Form ──────────────────────────────────────────────────────────────
with st.expander("➕ Add New Hat", expanded=False):
    with st.form("add_hat"):
        c1, c2, c3 = st.columns(3)
        style = c1.text_input("Style *", placeholder="e.g. Snapback, Dad Hat, Fitted")
        color = c2.text_input("Color *", placeholder="e.g. Black, Navy, White")
        size = c3.selectbox("Size *", SIZES)
        c4, c5 = st.columns(2)
        price = c4.number_input("Price ($) *", min_value=0.01, step=0.01, format="%.2f")
        qty = c5.number_input("Quantity in Stock *", min_value=0, step=1)
        submitted = st.form_submit_button("Add Hat")

        if submitted:
            errors = []
            if not style.strip():
                errors.append("Style is required.")
            if not color.strip():
                errors.append("Color is required.")
            if price <= 0:
                errors.append("Price must be greater than $0.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO hats (style, color, size, price, quantity_in_stock) VALUES (%s, %s, %s, %s, %s);",
                        (style.strip(), color.strip(), size, price, qty)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"Hat added: {style} ({color}, {size})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding hat: {e}")

# ── Search / Filter ───────────────────────────────────────────────────────────
st.subheader("Current Inventory")
search = st.text_input("🔍 Search by style or color", placeholder="e.g. Snapback or Black")

# ── Load & Display Hats ───────────────────────────────────────────────────────
try:
    conn = get_connection()
    cur = conn.cursor()

    if search.strip():
        cur.execute("""
            SELECT id, style, color, size, price, quantity_in_stock, created_at
            FROM hats
            WHERE style ILIKE %s OR color ILIKE %s
            ORDER BY style, color;
        """, (f"%{search.strip()}%", f"%{search.strip()}%"))
    else:
        cur.execute("""
            SELECT id, style, color, size, price, quantity_in_stock, created_at
            FROM hats ORDER BY style, color;
        """)

    hats = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Database error: {e}")
    hats = []

if not hats:
    st.info("No hats found. Add one above!")
else:
    # Header row
    h0, h1, h2, h3, h4, h5, h6, h7 = st.columns([1, 2, 2, 1.5, 1.5, 1.5, 1.2, 1.2])
    h0.markdown("**ID**")
    h1.markdown("**Style**")
    h2.markdown("**Color**")
    h3.markdown("**Size**")
    h4.markdown("**Price**")
    h5.markdown("**In Stock**")
    h6.markdown("**Edit**")
    h7.markdown("**Delete**")
    st.divider()

    for hat in hats:
        hat_id, style, color, size, price, qty, created_at = hat
        c0, c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 2, 1.5, 1.5, 1.5, 1.2, 1.2])
        c0.write(hat_id)
        c1.write(style)
        c2.write(color)
        c3.write(size)
        c4.write(f"${price:.2f}")
        c5.write(qty)

        if c6.button("✏️ Edit", key=f"edit_{hat_id}"):
            st.session_state[f"editing_hat"] = hat_id

        if c7.button("🗑️ Delete", key=f"del_{hat_id}"):
            st.session_state[f"confirm_del_hat"] = hat_id

    # ── Edit Form ──────────────────────────────────────────────────────────────
    editing_id = st.session_state.get("editing_hat")
    if editing_id:
        hat_data = next((h for h in hats if h[0] == editing_id), None)
        if hat_data:
            st.divider()
            st.subheader(f"Edit Hat #{editing_id}")
            with st.form("edit_hat"):
                c1, c2, c3 = st.columns(3)
                new_style = c1.text_input("Style *", value=hat_data[1])
                new_color = c2.text_input("Color *", value=hat_data[2])
                size_idx = SIZES.index(hat_data[3]) if hat_data[3] in SIZES else 0
                new_size = c3.selectbox("Size *", SIZES, index=size_idx)
                c4, c5 = st.columns(2)
                new_price = c4.number_input("Price ($) *", min_value=0.01, step=0.01, value=float(hat_data[4]), format="%.2f")
                new_qty = c5.number_input("Quantity in Stock *", min_value=0, step=1, value=int(hat_data[5]))
                col_save, col_cancel = st.columns(2)
                save = col_save.form_submit_button("💾 Save Changes")
                cancel = col_cancel.form_submit_button("Cancel")

                if save:
                    errors = []
                    if not new_style.strip():
                        errors.append("Style is required.")
                    if not new_color.strip():
                        errors.append("Color is required.")
                    if errors:
                        for e in errors:
                            st.error(e)
                    else:
                        try:
                            conn = get_connection()
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE hats SET style=%s, color=%s, size=%s, price=%s, quantity_in_stock=%s WHERE id=%s;",
                                (new_style.strip(), new_color.strip(), new_size, new_price, new_qty, editing_id)
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            del st.session_state["editing_hat"]
                            st.success("Hat updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating hat: {e}")

                if cancel:
                    del st.session_state["editing_hat"]
                    st.rerun()

    # ── Delete Confirmation ────────────────────────────────────────────────────
    confirm_id = st.session_state.get("confirm_del_hat")
    if confirm_id:
        hat_data = next((h for h in hats if h[0] == confirm_id), None)
        if hat_data:
            st.divider()
            st.warning(f"⚠️ Are you sure you want to delete **{hat_data[1]} ({hat_data[2]}, {hat_data[3]})**? This cannot be undone.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes, Delete It", key="confirm_yes_hat"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM hats WHERE id = %s;", (confirm_id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    del st.session_state["confirm_del_hat"]
                    st.success("Hat deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting hat: {e}")
            if c2.button("❌ Cancel", key="confirm_no_hat"):
                del st.session_state["confirm_del_hat"]
                st.rerun()
