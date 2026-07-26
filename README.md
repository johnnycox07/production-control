# Production Control API

Веб-приложение для управления сменными заданиями на производстве.

## Стек

- **API**: FastAPI + SQLAlchemy async + PostgreSQL
- **Очереди**: Celery + RabbitMQ
- **Кэш**: Redis
- **Хранилище**: MinIO (S3-compatible)

## Запуск

### 1. Подготовка

```bash
cp .env.example .env
```

### 2. Поднять инфраструктуру

```bash
docker compose up -d
```

### 3. Применить миграции

```bash
alembic upgrade head
```

### 4. Инициализировать MinIO buckets

```bash
python -m scripts.init_minio
```

### 5. Запустить API локально

```bash
uvicorn src.main:app --reload
```

## API документация

После запуска: `http://localhost:8000/docs`

## Сервисы

| Сервис        | URL                        |
|---------------|----------------------------|
| API           | http://localhost:8000      |
| Swagger       | http://localhost:8000/docs |
| RabbitMQ UI   | http://localhost:15672     |
| MinIO Console | http://localhost:9001      |
| Flower        | http://localhost:5555      |

## Основные эндпоинты

| Метод | URL                                  | Описание             |
|-------|--------------------------------------|----------------------|
| POST  | /api/v1/batches                      | Создать партии       |
| GET   | /api/v1/batches                      | Список партий        |
| GET   | /api/v1/batches/{id}                 | Получить партию      |
| PATCH | /api/v1/batches/{id}                 | Обновить партию      |
| POST  | /api/v1/products                     | Добавить продукт     |
| POST  | /api/v1/batches/{id}/aggregate       | Агрегировать продукт |
| POST  | /api/v1/batches/{id}/aggregate-async | Массовая агрегация   |
| GET   | /api/v1/tasks/{task_id}              | Статус задачи        |
| POST  | /api/v1/batches/import               | Импорт из Excel      |
| POST  | /api/v1/batches/export               | Экспорт в Excel      |
| POST  | /api/v1/webhooks                     | Создать webhook      |
| GET   | /api/v1/analytics/dashboard          | Статистика           |