"""One-shot schema alignment for legacy DBs (orders with inline customer columns)."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.database import engine


def ensure_orders_use_customers() -> None:
    """If `orders` still has customer_* columns, backfill `customers` and repoint FKs."""
    insp = inspect(engine)
    if "orders" not in insp.get_table_names():
        return

    order_cols = {c["name"] for c in insp.get_columns("orders")}
    if "customer_email" not in order_cols:
        return

    stmts = [
        text(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(320) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL DEFAULT '',
                shipping_address VARCHAR(1024) NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        ),
        text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_id UUID;"),
        text(
            """
            INSERT INTO customers (email, name, shipping_address)
            SELECT DISTINCT ON (customer_email)
                customer_email,
                customer_name,
                shipping_address
            FROM orders
            ORDER BY customer_email, created_at DESC
            ON CONFLICT (email) DO NOTHING;
            """
        ),
        text(
            """
            UPDATE orders o
            SET customer_id = c.id
            FROM customers c
            WHERE o.customer_id IS NULL
              AND c.email = o.customer_email;
            """
        ),
        text("ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;"),
        text(
            """
            DO $$
            BEGIN
                ALTER TABLE orders
                    ADD CONSTRAINT orders_customer_id_fkey
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT;
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
            """
        ),
        text(
            """
            ALTER TABLE orders DROP COLUMN IF EXISTS customer_email;
            ALTER TABLE orders DROP COLUMN IF EXISTS customer_name;
            ALTER TABLE orders DROP COLUMN IF EXISTS shipping_address;
            """
        ),
    ]

    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(stmt)
