import psycopg2
import streamlit as st

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

def init_db():
    """Create all tables if they don't exist, including status lookup tables."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hat_sizes (
            id SERIAL PRIMARY KEY,
            size_name VARCHAR(20) NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS order_statuses (
            id SERIAL PRIMARY KEY,
            status_name VARCHAR(20) NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS payment_statuses (
            id SERIAL PRIMARY KEY,
            status_name VARCHAR(20) NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS hats (
            id SERIAL PRIMARY KEY,
            style VARCHAR(100) NOT NULL,
            color VARCHAR(50) NOT NULL,
            size VARCHAR(10) NOT NULL,
            price NUMERIC(10,2) NOT NULL,
            quantity_in_stock INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            order_date TIMESTAMP DEFAULT NOW(),
            status VARCHAR(20) NOT NULL DEFAULT 'Pending',
            payment_status VARCHAR(20) NOT NULL DEFAULT 'Unpaid',
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            hat_id INTEGER NOT NULL REFERENCES hats(id),
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price NUMERIC(10,2) NOT NULL
        );
    """)
    conn.commit()

    # Seed lookup tables if empty
    cur.execute("SELECT COUNT(*) FROM hat_sizes;")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO hat_sizes (size_name) VALUES (%s) ON CONFLICT DO NOTHING;",
            [("One Size",), ("S/M",), ("L/XL",), ("Fitted - S",), ("Fitted - M",), ("Fitted - L",), ("Fitted - XL",)]
        )

    cur.execute("SELECT COUNT(*) FROM order_statuses;")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO order_statuses (status_name) VALUES (%s) ON CONFLICT DO NOTHING;",
            [("Pending",), ("Shipped",), ("Delivered",), ("Cancelled",)]
        )

    cur.execute("SELECT COUNT(*) FROM payment_statuses;")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO payment_statuses (status_name) VALUES (%s) ON CONFLICT DO NOTHING;",
            [("Unpaid",), ("Paid",), ("Refunded",)]
        )

    conn.commit()
    cur.close()
    conn.close()


def get_sizes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT size_name FROM hat_sizes ORDER BY id;")
    rows = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def get_order_statuses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT status_name FROM order_statuses ORDER BY id;")
    rows = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def get_payment_statuses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT status_name FROM payment_statuses ORDER BY id;")
    rows = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows
