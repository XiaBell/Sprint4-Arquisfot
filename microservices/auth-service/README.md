# Auth Service - Módulo de Seguridad y Roles

Microservicio Node.js/Express que valida y decodifica tokens JWT de Auth0.

## Endpoints

### POST /api/v1/auth/validate
Valida un token JWT y extrae el rol del usuario.

**Request:**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (success):**
```json
{
  "isValid": true,
  "rol": "GESTOR",
  "userId": "auth0|123456",
  "email": "gestor@provesi.com"
}
```

**Response (error):**
```json
{
  "isValid": false,
  "error": "Token expired"
}
```

### POST /api/v1/auth/decode
Decodifica un token sin verificar (solo para debugging).

### GET /health
Health check del servicio.

## Configuración

Variables de entorno:
- `PORT`: Puerto del servicio (default: 3000)
- `AUTH0_DOMAIN`: Dominio de Auth0
- `AUTH0_AUDIENCE`: Audience de Auth0

## Ejecución

```bash
npm install
npm start
```

O con Docker:
```bash
docker-compose up
```

