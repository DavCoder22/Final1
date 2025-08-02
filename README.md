# Student Registration Microservices Project

Este proyecto implementa un sistema de registro de estudiantes compuesto por microservicios con **FastAPI**, bases de datos **PostgreSQL** y **MongoDB**, y un **API Gateway Nginx**. Todo se orquesta con **Docker Compose** para facilitar la ejecución local y el despliegue.

## Arquitectura

```
┌────────────┐      ┌──────────────────────┐
│  Cliente   │──▶──▶│   Nginx Gateway :80  │
└────────────┘      │  • /register 8001    │
                    │  • /attendance 8002  │
                    │  • /report 8003      │
                    └──────────────────────┘
                           ▲      ▲      ▲
                           │      │      │
        ┌──────────────────┼──────┼──────┼──────────────────┐
        │                  │      │      │                  │
┌─────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│ RegisterService │ │ AttendanceSvc │ │  ReportSvc     │  │
│  FastAPI 8001   │ │ FastAPI 8002  │ │ FastAPI 8003   │  │
└───────▲─────────┘ └──────▲────────┘ └────────▲────────┘  │
        │                  │                     │         │
        │                  │                     │         │
   ┌────┴────┐        ┌────┴────┐          ┌─────┴────┐    │
   │ Postgres│        │  Mongo  │          │ Postgres │    │
   │  5432   │        │  27017  │          │  5432    │    │
   └─────────┘        └─────────┘          └──────────┘    │
        Backend Network (Docker)                            │
└────────────────────────────────────────────────────────────┘
```

## Requisitos previos

* Docker >= 20.10
* Docker Compose >= 2.0

## Variables de entorno
Crea un archivo `.env` en la raíz del proyecto con, por ejemplo:

```
POSTGRES_USER=postgrest1
POSTGRES_PASSWORD=TuPasswordSegura
POSTGRES_DB=studentdb
MONGO_INITDB_ROOT_USERNAME=mongo1
MONGO_INITDB_ROOT_PASSWORD=TuPasswordSegura
```

Docker Compose las usará automáticamente.

## Ejecución local

```bash
git clone <repo>
cd Final1
cp .env.example .env   # o crea tu propio .env
# Construir e iniciar todos los servicios en segundo plano
docker compose up -d --build

# Ver logs
docker compose logs -f nginx-gateway
```

Accede a la API Gateway en `http://localhost:8080`.

## Endpoints principales

| Servicio | Puerto/Path | Descripción |
|----------|-------------|-------------|
| Register | `:8001` vía `/register` | Registro de estudiantes |
| Attendance | `:8002` vía `/attendance` | Control de asistencias |
| Report | `:8003` vía `/report` | Reportes y consultas |

## Despliegue en Producción

1. Proveer una máquina con Docker (por ejemplo, Ubuntu 22.04 en AWS EC2).
2. Clonar el repositorio y definir el `.env` con secretos reales.
3. (Opcional) Subir las imágenes a un registry y reemplazar `build:` por `image:` en `docker-compose.yml`.
4. Ejecutar:
   ```bash
   docker compose pull   # si usas images
   docker compose up -d
   ```
5. Configurar un registro DNS y un certificado TLS (Let’s Encrypt) apuntando al puerto `8080`.
6. Implementar un pipeline CI/CD (GitHub Actions) para construir y desplegar automáticamente.

## Comandos útiles

```bash
# Listar contenedores
docker compose ps

# Escalar un servicio (ej. 3 réplicas de report-service)
docker compose up -d --scale report-service=3

# Detener y eliminar todo
docker compose down -v
```

## Estructura del repositorio

```
Final1/
├── StudentRegistration/
│   ├── register-service/
│   ├── attendance-service/
│   └── report-service/
├── nginx/
├── docker-compose.yml
├── requirements.txt
└── README.md  <-- (este archivo)
```

## Licencia

MIT
