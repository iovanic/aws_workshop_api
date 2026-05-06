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
                phone_number VARCHAR(32) NOT NULL DEFAULT '',
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


def ensure_customer_phone_column() -> None:
    """Añade `phone_number` y migra filas antiguas con `\\nTel:` en `shipping_address`."""
    insp = inspect(engine)
    if "customers" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("customers")}
    if "phone_number" not in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE customers ADD COLUMN phone_number "
                    "VARCHAR(32) NOT NULL DEFAULT '';"
                )
            )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE customers
                SET
                    phone_number = left(
                        trim(split_part(shipping_address, E'\\nTel:', 2)),
                        32
                    ),
                    shipping_address = trim(split_part(shipping_address, E'\\nTel:', 1))
                WHERE shipping_address LIKE E'%\\nTel:%';
                """
            )
        )


def _pg_att_typname(conn, table: str, column: str, schema: str = "public") -> str | None:
    """Nombre interno de tipo PostgreSQL (`int4`, `numeric`, …) para una columna."""
    return conn.execute(
        text(
            """
            SELECT t.typname::text
            FROM pg_catalog.pg_attribute a
            INNER JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
            INNER JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            INNER JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
            WHERE n.nspname = :schema
              AND c.relkind = 'r'
              AND c.relname = :table
              AND a.attname = :column
              AND a.attnum > 0
              AND NOT a.attisdropped
            """
        ),
        {"schema": schema, "table": table, "column": column},
    ).scalar_one_or_none()


def ensure_product_prices_decimal() -> None:
    """Pasa `products.price` y `order_items.unit_price` de enteros (céntimos) a NUMERIC(12,2) en EUR.

    Usa `pg_catalog` + `typname` (`int4`, `int8`, …), alineado con lo que muestran DBeaver/psql,
    en lugar de depender solo de `information_schema` o del inspector de SQLAlchemy.
    """
    int_types = frozenset({"int2", "int4", "int8"})

    with engine.begin() as conn:
        tn = _pg_att_typname(conn, "products", "price")
        if tn is not None and tn in int_types:
            conn.execute(
                text(
                    """
                    ALTER TABLE products
                    ALTER COLUMN price TYPE NUMERIC(12,2)
                    USING (ROUND(price::numeric / 100, 2));
                    """
                )
            )

    with engine.begin() as conn:
        tn = _pg_att_typname(conn, "order_items", "unit_price")
        if tn is not None and tn in int_types:
            conn.execute(
                text(
                    """
                    ALTER TABLE order_items
                    ALTER COLUMN unit_price TYPE NUMERIC(12,2)
                    USING (ROUND(unit_price::numeric / 100, 2));
                    """
                )
            )
