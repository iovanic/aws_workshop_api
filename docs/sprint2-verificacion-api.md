# Comprobaciones API — Sprint 2 (next-drones-api)

Comandos de ejemplo con **`curl`**. Ajusta la URL base a tu entorno (local, EC2 público, etc.).

```bash
export API_BASE="http://localhost:8000"
# Ejemplo taller (sustituye por tu DNS:puerto si aplica):
# export API_BASE="http://ec2-98-80-151-84.compute-1.amazonaws.com:8000"
```

> **Orden al borrar:** primero **pedidos** (liberan líneas y referencias a productos en pedidos ya borrados), luego **cliente** (solo si no tiene pedidos), luego **producto** (solo si no aparece en ningún `order_items`).

---

## 1. Salud del servicio

```bash
curl -fsS "$API_BASE/health"
```

---

## 2. Ver productos

```bash
curl -fsS "$API_BASE/products"
```

Detalle por id:

```bash
curl -fsS "$API_BASE/products/skhawk-x1"
```

---

## 3. Crear un producto

```bash
curl -fsS -X POST "$API_BASE/products" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-drone-1",
    "name": "Drone de prueba",
    "tagline": "Solo taller",
    "description": "Producto ficticio para comprobar POST.",
    "price": 9999,
    "images": ["/images/test/1.png"]
  }'
```

---

## 4. Crear un cliente

```bash
curl -fsS -X POST "$API_BASE/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cliente.taller@example.com",
    "name": "Cliente Taller",
    "shipping_address": "Calle Falsa 123"
  }'
```

Guardar el `id` del cliente (UUID) para borrarlo después (requiere `python3`):

```bash
export CUSTOMER_ID="$(
  curl -fsS -X POST "$API_BASE/customers" \
    -H "Content-Type: application/json" \
    -d '{"email":"otro.cliente@example.com","name":"Otro","shipping_address":"X"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])"
)"
echo "$CUSTOMER_ID"
```

---

## 5. Ver clientes

```bash
curl -fsS "$API_BASE/customers"
```

---

## 6. Crear un pedido

Usa `product_id` existente (por ejemplo uno del seed: `skhawk-x1`). El pedido **crea o actualiza** el cliente por email (igual que antes); si quieres probar solo el flujo de `POST /customers`, usa otro email aquí.

```bash
curl -fsS -X POST "$API_BASE/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "pedido@example.com",
    "customer_name": "Comprador Pedido",
    "shipping_address": "Envío 456",
    "items": [
      { "product_id": "skhawk-x1", "quantity": 1 }
    ]
  }'
```

Guardar el `id` del pedido (UUID) (requiere `python3`):

```bash
export ORDER_ID="$(
  curl -fsS -X POST "$API_BASE/orders" \
    -H "Content-Type: application/json" \
    -d '{
      "customer_email":"pedido@example.com",
      "customer_name":"Comprador Pedido",
      "shipping_address":"Envío 456",
      "items":[{"product_id":"skhawk-x1","quantity":1}]
    }' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])"
)"
echo "$ORDER_ID"
```

---

## 7. Ver el pedido (y listar pedidos)

Por id:

```bash
curl -fsS "$API_BASE/orders/${ORDER_ID}"
```

Listado:

```bash
curl -fsS "$API_BASE/orders"
```

---

## 8. Eliminar pedido

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" -X DELETE "$API_BASE/orders/${ORDER_ID}"
```

Esperado: **`204`** (sin cuerpo).

---

## 9. Eliminar cliente

Solo si **no tiene pedidos** (si tiene, la API responde **409**).

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" -X DELETE "$API_BASE/customers/${CUSTOMER_ID}"
```

Ejemplo con UUID literal:

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" -X DELETE \
  "$API_BASE/customers/00000000-0000-0000-0000-000000000000"
```

---

## 10. Eliminar producto

Solo si **no está referenciado** en ningún `order_items` (si lo está, **409**).

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" -X DELETE "$API_BASE/products/test-drone-1"
```

---

## Referencia rápida de rutas

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servicio |
| `GET` | `/products` | Listar productos |
| `GET` | `/products/{id}` | Detalle producto |
| `POST` | `/products` | Crear producto |
| `DELETE` | `/products/{id}` | Borrar producto |
| `GET` | `/customers` | Listar clientes |
| `POST` | `/customers` | Crear cliente |
| `DELETE` | `/customers/{uuid}` | Borrar cliente (sin pedidos) |
| `GET` | `/orders` | Listar pedidos |
| `POST` | `/orders` | Crear pedido (+ cliente por email) |
| `GET` | `/orders/{uuid}` | Detalle pedido |
| `DELETE` | `/orders/{uuid}` | Borrar pedido |

---

## Notas

- **`curl -f`**: falla si el código HTTP indica error (4xx/5xx), útil en scripts.
- La respuesta JSON sale en bruto en la terminal; puedes copiar el `id` a mano o usar los bloques con `python3` de arriba.
- Tras cambiar código en el repo, vuelve a **build/push** la imagen y **reinicia** el contenedor en EC2 para que estos endpoints estén disponibles en el taller.
