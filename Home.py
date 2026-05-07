# AI Prompts & Process Log — leodropped Hat Business Tracker

This document records every prompt given to Claude (claude-sonnet-4-6) during this project, along with notes on what worked and what needed adjustment.

---

## Prompt 1 — Initial Project Setup & Topic Selection

**Prompt:**
> I have a class project that requires building a Streamlit web app backed by a PostgreSQL database. Here is the assignment: [pasted full directions from Systems-Project-1-directions.md]. I want to build a system for my hat business called leodropped. We sell stock hats in different styles, colors, and sizes. I need to track customer orders and inventory.

**What the AI did:**
Claude asked clarifying questions about the type of hats (stock vs custom) and what I needed to track day-to-day. After answering, it proposed a 4-table schema: hats, customers, orders, and order_items as a junction table.

**What worked:** The table structure suggestion was solid and matched the many-to-many requirement right away.

**What I had to fix:** Nothing at this stage — the planning conversation was helpful before any code was written.

---

## Prompt 2 — Full Planning Documents

**Prompt:**
> Generate all my planning documents for this project: system description, entity list with all columns and constraints, relationships, page-by-page plan for all 4 pages, validation rules for every form, ERD code for dbdiagram.io, and the full SQL CREATE TABLE statements. The system is for leodropped — a hat business tracking inventory (hats table with style, color, size, price, quantity), customers, orders, and order_items as a junction table.

**What the AI did:**
Generated a complete Word document (.docx) with all planning sections, properly formatted tables for entity attributes, bullet-pointed relationships and page plans, validation rule tables for every form, and dbdiagram.io code for the ERD.

**What worked:** The entity list was detailed and matched the final schema. The SQL CREATE TABLE statements were accurate and included proper foreign keys and ON DELETE CASCADE.

**What I had to fix:** Added the lookup tables (hat_sizes, order_statuses, payment_statuses) later when I realized the directions required dynamic dropdowns — no hard-coded Python lists allowed.

---

## Prompt 3 — Database Connection File (db.py)

**Prompt:**
> Create a db.py file for my Streamlit app that connects to PostgreSQL using psycopg2 and st.secrets["DB_URL"]. Include an init_db() function that creates all tables if they don't exist: hats, customers, orders, order_items, and three lookup tables: hat_sizes, order_statuses, payment_statuses. The lookup tables should auto-seed with default values (sizes like One Size/S/M/L/XL, statuses like Pending/Shipped/Delivered/Cancelled, payment statuses like Unpaid/Paid/Refunded) if empty. Also include helper functions get_sizes(), get_order_statuses(), and get_payment_statuses() that each query their lookup table and return a list of strings.

**What the AI did:**
Generated the full db.py with all tables, seeding logic, and helper functions. Used ON CONFLICT DO NOTHING for safe re-seeding.

**What worked:** Everything on first try. The seeding logic was clean.

**What I had to fix:** Nothing.

---

## Prompt 4 — Home Dashboard (Home.py)

**Prompt:**
> Create Home.py for a Streamlit app called leodropped. It should: call init_db() on load, display 5 st.metric() cards (total hat products, total customers, total orders, total paid revenue, pending orders count), show a table of the 10 most recent orders with customer name/date/status/payment/item count, and show a bar chart of orders grouped by status. Use psycopg2 with parameterized queries. Connect using st.secrets["DB_URL"]. Show user-friendly error messages if the DB connection fails.

**What the AI did:**
Generated the full dashboard page with all metrics, the recent orders table using pandas, and a bar chart using st.bar_chart().

**What worked:** Metrics and recent orders table worked perfectly.

**What I had to fix:** The revenue metric needed a COALESCE to avoid returning None when no paid orders exist yet — added `COALESCE(SUM(...), 0)` in the SQL.

---

## Prompt 5 — Manage Inventory Page

**Prompt:**
> Create pages/1_Manage_Inventory.py for my leodropped Streamlit app. It should:
> 1. Import get_sizes() from db.py and use it for the size dropdown — no hard-coded lists.
> 2. Have an Add Hat form (style, color, size dropdown, price, quantity) inside st.expander. Validate: style and color required, price > 0, quantity >= 0.
> 3. A search bar that filters hats by style or color using ILIKE.
> 4. A table of all hats with Edit and Delete buttons per row using st.columns().
> 5. Edit button opens a pre-filled edit form. Save updates the record.
> 6. Delete button shows a confirmation before deleting.
> Use parameterized queries throughout. No f-strings in SQL. Use st.session_state to track which row is being edited or deleted.

**What the AI did:**
Generated the full page with all features. Used session_state correctly for tracking edit/delete state.

**What worked:** Add form, search, and delete confirmation all worked on first try.

**What I had to fix:** The edit form's size dropdown needed `index=` set to the current hat's size — had to find the current size in the SIZES list using `.index()` with a fallback default.

---

## Prompt 6 — Manage Customers Page

**Prompt:**
> Create pages/2_Manage_Customers.py for leodropped. It should:
> 1. Add Customer form: first_name, last_name, email (required, validate with regex ^[^@\s]+@[^@\s]+\.[^@\s]+$), phone (optional, must be 10 digits if provided).
> 2. Search bar filtering by first name, last name, or email using ILIKE.
> 3. Table of all customers with Edit and Delete buttons per row.
> 4. Edit form pre-filled with current values.
> 5. Delete with confirmation. Note: deleting a customer should mention it will also remove their orders.
> Use st.session_state for edit/delete tracking. Parameterized queries only.

**What the AI did:**
Generated complete customer management page with regex validation for both email and phone.

**What worked:** All validation, search, and CRUD worked first try.

**What I had to fix:** The duplicate email error message needed a specific check for "unique" in the exception string to show a friendly message instead of a raw psycopg2 error.

---

## Prompt 7 — Manage Orders Page

**Prompt:**
> Create pages/3_Manage_Orders.py for leodropped. It should:
> 1. Import get_order_statuses() and get_payment_statuses() from db.py — no hard-coded status lists.
> 2. Create Order form: select customer from dropdown (pulled from customers table), select status (from order_statuses table), select payment_status (from payment_statuses table), notes field, select hat (from hats where quantity > 0), quantity input.
> 3. On order creation: insert the order, insert the order_item, deduct stock from hats table. Validate quantity does not exceed current stock.
> 4. Filter orders by status (dropdown).
> 5. Table of all orders with View / Edit / Delete buttons.
> 6. View opens a detail panel showing all items and order total.
> 7. Edit allows changing status, payment_status, and notes.
> 8. Delete with confirmation — cascades to order_items automatically.
> Parameterized queries only. Use st.session_state for panel tracking.

**What the AI did:**
Generated the full orders page with all CRUD, the order detail view, and stock deduction logic.

**What worked:** Order creation with stock deduction, filtering, and delete cascade all worked.

**What I had to fix:** The View detail panel needed an explicit "Close" button since re-clicking View on the same order didn't toggle it off. Also added a stock validation check (quantity > stock) that wasn't in the first draft.

---

## Overall Notes

**Where AI saved the most time:** Generating the boilerplate for forms, parameterized queries, and session_state patterns. Every page followed the same structure so once the first one was right, subsequent prompts were faster.

**Where I had to iterate:** Dynamic dropdowns were the biggest mid-project change. The original code used hard-coded Python lists (SIZES, ORDER_STATUSES, etc.), which violated the assignment requirement. Had to refactor db.py to add lookup tables and update all pages to call get_sizes(), get_order_statuses(), and get_payment_statuses() instead.

**What I'd do differently:** Specify the dynamic dropdown requirement in the very first prompt so the lookup tables are in the schema from the start. Adding them mid-project required updating db.py, all three pages, and the design documents.
