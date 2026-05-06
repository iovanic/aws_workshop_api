# Tutorial — API con autenticación Cognito (Sprint 3)

Aprende a hacer **las mismas peticiones que en el Sprint 2**, pero ahora a través de **API Gateway** y con un **token de usuario** que te identifica.

---

## ¿Qué cambia respecto al Sprint 2?

| Sprint 2 | Sprint 3 |
|----------|----------|
| URL directa al servidor (`http://....:8000`) | URL de API Gateway (`https://....execute-api....amazonaws.com/prod`) |
| Sin autenticación — cualquiera podía llamar | Necesitas **iniciar sesión** y añadir un token a cada petición |

La **API FastAPI no cambia** — el código es el mismo. Solo añadimos una capa delante (API Gateway + Cognito) que comprueba quién eres antes de dejar pasar tu petición.

---

## Tus URLs y datos del taller

Copia y pega este bloque completo al principio de tu terminal. Lo usarás en todos los pasos siguientes:

```bash
# La nueva URL pública (a través de API Gateway)
export API_GW="https://br08qmovv8.execute-api.us-east-1.amazonaws.com/prod"

# Datos de Cognito (el servicio de identidad de AWS)
export POOL_ID="us-east-1_QEkfKcnei"
export CLIENT_ID="6amp2uc7u4e9c3rh8ifeur17hh"
export REGION="us-east-1"

# Opcional (útil en consola / depuración): REST API id
export REST_API_ID="br08qmovv8"
```

> El `CLIENT_ID` es el identificador del "cliente" de la tienda en Cognito. No tiene secreto porque es una app pública (cualquier alumno puede registrarse).

> **Si recreas recursos en otra cuenta o sesión de lab**, sustituye `API_GW`, `POOL_ID`, `CLIENT_ID` y `REST_API_ID` por los valores que obtengas al volver a provisionar API Gateway Edge y Cognito (`create-rest-api`, `create-user-pool`, `create-user-pool-client`).

> **Usuario de prueba (referencia, despliegue taller):** `workshop.test@example.com` / `Taller2026!` — si ya existe en tu pool, puedes ir directamente al **Paso 2** con `MI_EMAIL` y `MI_PASSWORD` iguales a esos valores. Si no, sigue el **Paso 1** con tu propio email.

En el pool de referencia el taller permite **autoregistro** (`AllowAdminCreateUserOnly=false`). Si tu cuenta tiene **deny** en `AdminCreateUser` pero **no** en `sign-up`, puedes registrarte con `aws cognito-idp sign-up` usando el mismo `CLIENT_ID` y luego confirmar el usuario según lo que permita tu rol (p. ej. `admin-confirm-sign-up` o verificación por email).

---

## Paso 1 — Crear tu usuario (una sola vez)

El **instructor** crea los usuarios del taller con estos dos comandos. Sustituye `TU_EMAIL` y `TU_PASSWORD` por los datos que el instructor te indique (o usa los de ejemplo si estás tú solo):

```bash
export MI_EMAIL="alumno.taller@example.com"
export MI_PASSWORD="Taller2026!"

# Crear el usuario (el instructor ejecuta esto)
aws cognito-idp admin-create-user \
  --region "$REGION" \
  --user-pool-id "$POOL_ID" \
  --username "$MI_EMAIL" \
  --user-attributes Name=email,Value="$MI_EMAIL" Name=email_verified,Value=true \
  --temporary-password "Temp1234!" \
  --message-action SUPPRESS

# Establecer la contraseña definitiva (el instructor ejecuta esto)
aws cognito-idp admin-set-user-password \
  --region "$REGION" \
  --user-pool-id "$POOL_ID" \
  --username "$MI_EMAIL" \
  --password "$MI_PASSWORD" \
  --permanent
```

Cuando veas `{}` o ningún error, el usuario está listo.

> **¿Por qué el instructor crea el usuario?**  
> En el taller usamos el flujo de administrador para evitar tener que verificar el correo electrónico (en un proyecto real los usuarios se registran solos y reciben un email de verificación).

### Si aparece `AccessDeniedException` con `voc-cancel-cred` (AWS Academy / Vocareum)

No es un fallo del comando: tu cuenta de laboratorio tiene una **política IAM con denegación explícita** (suele llamarse algo como `voc-cancel-cred`) que bloquea APIs de administración de Cognito: `AdminCreateUser`, `DescribeUserPool`, etc. Ocurre en algunos estados del lab (credenciales revocadas, sesión cerrada, restricciones del curso). **No se puede solucionar** cambiando el comando ni usando otro navegador.

**Qué hacer:**

1. Cierra el laboratorio en AWS Academy / Vocareum y **abre uno nuevo** (sesión limpia).
2. Pregunta al **instructor** del curso o al soporte de Academy si tu cuenta está en modo restringido.
3. Si otro miembro del equipo **sí** puede usar Cognito en la consola, que cree los usuarios o que todos usen el mismo pool compartido según las normas del taller.

Mientras tanto **no podrás** completar el Paso 1 ni abrir el user pool en la consola si también falla `DescribeUserPool`.

---

## Paso 2 — Iniciar sesión y obtener el token

Ahora **tú** haces login y guardas el token en una variable:

```bash
export TOKEN=$(aws cognito-idp initiate-auth \
  --region "$REGION" \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "$CLIENT_ID" \
  --auth-parameters USERNAME="$MI_EMAIL",PASSWORD="$MI_PASSWORD" \
  --query 'AuthenticationResult.IdToken' \
  --output text)

echo "Token guardado: ${TOKEN:0:60}..."
```

Si ves una cadena larga de letras y números → **login correcto**.  
Si ves un error → revisa el email y la contraseña.

> **¿Qué es ese token?**  
> Es un **JWT** (JSON Web Token): una cadena firmada por AWS que prueba que eres tú. Expira en **1 hora**. Si pasa ese tiempo, vuelve a ejecutar el `export TOKEN=$(aws cognito-idp...)` de arriba.

---

## Paso 3 — Usar el token en cada petición

A partir de ahora añades `-H "Authorization: Bearer $TOKEN"` a cada `curl`.

**Regla simple:** ¿la petición va a `$API_GW`? Pon el token. Sin él recibirás un error `401 Unauthorized`.

Comprueba que sin cabecera `Authorization` la API no responde en claro:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" "$API_GW/health"
```

Deberías ver **`401`**.

---

## Comprobaciones (equivalente al Sprint 2)

> **Orden al borrar** igual que antes: primero **pedidos**, luego **cliente** (si no tiene pedidos), luego **producto** (si no está en ningún pedido).

---

### 1. Salud del servicio

```bash
curl -fsS -H "Authorization: Bearer $TOKEN" "$API_GW/health"
```

Respuesta esperada: `{"status":"ok"}`

---

### 2. Ver todos los productos

```bash
curl -fsS -H "Authorization: Bearer $TOKEN" "$API_GW/products"
```

---

### 3. Ver un producto por ID

```bash
curl -fsS -H "Authorization: Bearer $TOKEN" "$API_GW/products/skhawk-x1"
```

---

### 4. Crear un producto

```bash
curl -fsS -X POST "$API_GW/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-drone-1",
    "name": "Drone de prueba",
    "tagline": "Solo taller",
    "description": "Producto ficticio para comprobar POST.",
    "price": 99.99,
    "images": ["/images/test/1.png"]
  }'
```

---

### 5. Crear un cliente

```bash
curl -fsS -X POST "$API_GW/customers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cliente.taller@example.com",
    "name": "Cliente Taller",
    "shipping_address": "Calle Falsa 123"
  }'
```

Guardar el `id` del cliente para borrarlo después:

```bash
export CUSTOMER_ID="$(
  curl -fsS -X POST "$API_GW/customers" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"email":"otro.cliente@example.com","name":"Otro","shipping_address":"X"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])"
)"
echo "$CUSTOMER_ID"
```

---

### 6. Ver clientes

```bash
curl -fsS -H "Authorization: Bearer $TOKEN" "$API_GW/customers"
```

---

### 7. Crear un pedido

```bash
curl -fsS -X POST "$API_GW/orders" \
  -H "Authorization: Bearer $TOKEN" \
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

Guardar el `id` del pedido:

```bash
export ORDER_ID="$(
  curl -fsS -X POST "$API_GW/orders" \
    -H "Authorization: Bearer $TOKEN" \
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

### 8. Ver el pedido (y listar pedidos)

Por id:

```bash
curl -fsS -H "Authorization: Bearer $TOKEN" "$API_GW/orders/$ORDER_ID"
```

Listado completo:

```bash
curl -fsS -H "Authorization: Bearer $TOKEN" "$API_GW/orders"
```

---

### 9. Eliminar pedido

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" \
  -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "$API_GW/orders/$ORDER_ID"
```

Esperado: **`204`**

---

### 10. Eliminar cliente

Solo si **no tiene pedidos activos** (si tiene → `409 Conflict`):

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" \
  -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "$API_GW/customers/$CUSTOMER_ID"
```

---

### 11. Eliminar producto

Solo si **no está en ningún pedido** (si está → `409 Conflict`):

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" \
  -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "$API_GW/products/test-drone-1"
```

---

## Referencia rápida

| Método | Ruta | Token |
|--------|------|--------|
| `GET` | `/health` | Sí |
| `GET` | `/products` | Sí |
| `GET` | `/products/{id}` | Sí |
| `POST` | `/products` | Sí |
| `DELETE` | `/products/{id}` | Sí |
| `GET` | `/customers` | Sí |
| `POST` | `/customers` | Sí |
| `DELETE` | `/customers/{uuid}` | Sí |
| `GET` | `/orders` | Sí |
| `POST` | `/orders` | Sí |
| `GET` | `/orders/{uuid}` | Sí |
| `DELETE` | `/orders/{uuid}` | Sí |

**Todas las rutas requieren el mismo token.** Si recibes `401`, el token caducó — vuelve a hacer login (Paso 2).

---

## Errores frecuentes

| Error | Causa | Solución |
|-------|-------|----------|
| `401 Unauthorized` | Token ausente, caducado o incorrecto | Vuelve a ejecutar el Paso 2 |
| `401 Unauthorized` (llevas `Authorization: Bearer …`) | Suele ser el **access token**; el authorizer `COGNITO_USER_POOLS` espera el **ID token** | Usa `AuthenticationResult.IdToken` en el `export TOKEN=...` |
| `AccessDeniedException` + `voc-cancel-cred` | Cuenta de lab (Academy) con **deny explícito** en APIs de Cognito | Nuevo lab / instructor / soporte; no se arregla con el comando |
| `403 Forbidden` | El token no tiene permisos (distinto pool o client) | Comprueba que `CLIENT_ID` es el correcto |
| `409 Conflict` | Intentas borrar algo que tiene dependencias | Borra primero los pedidos, luego el cliente, luego el producto |
| `422 Unprocessable Entity` | JSON mal formado o campos que faltan | Revisa el cuerpo del `-d '...'` |
| `curl: (22) ... 4xx/5xx` | La opción `-f` hace que curl falle en errores HTTP | Quita `-f` para ver el mensaje de error completo |

---

## Notas finales

- **El token dura 1 hora.** Si pasa ese tiempo, vuelve al Paso 2.
- Puedes decodificar tu token en [jwt.io](https://jwt.io) para ver qué información contiene (nombre, email, expiración…).
- Tras cambiar código en el repo, sigue haciendo **build → push ECR → redeploy en EC2** — el Gateway simplemente reenvía al mismo contenedor.
- El authorizer de API Gateway valida el **ID token** (`IdToken` de `initiate-auth`), no el access token.
