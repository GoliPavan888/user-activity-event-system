# User Activity Event System

A microservice-based event tracking system built with FastAPI, RabbitMQ, and MySQL, containerized using Docker Compose.

The system collects user activity events, queues them through RabbitMQ, and stores them in a MySQL database via a consumer service.

---

## Architecture Overview

```
Client → Producer API → RabbitMQ Queue → Consumer Service → MySQL Database
```

---

## Services

### Producer Service
- FastAPI service exposing a REST endpoint
- Validates payloads against `UserActivityEvent` model
- Publishes messages to the `user_activity_events` RabbitMQ queue (direct exchange)

### RabbitMQ
- Standalone broker running in a container
- Queue name: `user_activity_events` (durable)
- Configuration is driven by environment variables to avoid hard‑coding

### Consumer Service
- FastAPI application, but the HTTP interface is minimal
- Background thread opens a long‑lived RabbitMQ consumer
- Implements retry logic and message acknowledgements
- Persists events into MySQL table `user_activities`

### MySQL Database
- Initialized via `db/init.sql` on startup
- Schema defined with appropriate types (INT for `user_id`, DATETIME, JSON metadata)
- Volume mounting ensures the table is created automatically

---

## Project Structure

```
user-activity-event-system/
├── producer-service/
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
├── consumer-service/
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   ├── producer/
│   └── consumer/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Technologies Used

- **FastAPI** - Modern Python web framework
- **RabbitMQ** - Message broker
- **MySQL** - Relational database
- **Docker & Docker Compose** - Containerization
- **Pika** - RabbitMQ client
- **Pytest** - Testing framework

---

## Setup Instructions

### 1. Clone Repository

```
bash
git clone <repo-url>
cd user-activity-event-system
```

### 2. Create Environment File

Copy example env file:

```
bash
cp .env.example .env
```

Update values if needed.

### 3. Start Services

```
bash
docker-compose up --build
```

Or run in background:

```
bash
docker-compose up -d --build
```

---

## Service Endpoints

| Service | URL |
|---------|-----|
| Producer API Docs | http://localhost:8000/docs |
| Consumer Health Check | http://localhost:8001/health |
| RabbitMQ Dashboard | http://localhost:15672 |

**RabbitMQ Dashboard Default Login:**
- Username: `guest`
- Password: `guest`

---

## Sending an Event

The producer API expects a JSON body matching the `UserActivityEvent` schema:

```json
{
  "user_id": 123,
  "event_type": "page_view",
  "timestamp": "2023-10-27T10:00:00Z",
  "metadata": {"page_url": "/products/xyz", "session_id": "abc123"}
}
```

Example curl request using the correct types:

```bash
curl -X POST http://localhost:8000/api/v1/events/track \
  -H "Content-Type: application/json" \
  -d '{
        "user_id": 1,
        "event_type": "login",
        "timestamp": "2026-02-17T15:10:00Z",
        "metadata": {"ip": "127.0.0.1"}
      }'
```

The API will respond with **202 Accepted** if the event is valid and enqueued. Invalid payloads return **400 Bad Request** with details.
---

## Verify Event Stored

Enter MySQL container:

```
bash
docker-compose exec mysql mysql -u root -p
```

Then:

```
sql
USE user_activity_db;
SELECT * FROM user_activities;
```

---

## Running Tests

### Producer tests

```
bash
docker-compose exec producer-service pytest tests/producer
```
### Consumer tests

```
bash
docker-compose exec consumer-service pytest tests/consumer
```

---

## Example Architecture Diagram

```mermaid
flowchart LR
    Client -->|HTTP POST| Producer[Producer API]
    Producer -->|AMQP| RabbitMQ["RabbitMQ\n(user_activity_events)"]
    RabbitMQ -->|consume| Consumer[Consumer Service]
    Consumer -->|INSERT| MySQL[MySQL\n(user_activities)]
```

---

## Stopping Services

```
bash
docker-compose down
```

Remove volumes:

```
bash
docker-compose down -v
```

---

## Features Implemented

- ✅ Event ingestion API
- ✅ Message queue processing
- ✅ Consumer event storage
- ✅ Dockerized services
- ✅ Retry handling
- ✅ Health checks
- ✅ Automated tests

---

## Future Improvements

- [ ] Authentication for API (out-of-scope but easily added)
- [x] Retry logic and malformed-message handling in consumer
- [x] Health checks that verify dependency connectivity
- [ ] Analytics/stream processing service downstream
- [ ] More sophisticated dead-letter queue or backoff strategy

---

## Challenges & Design Decisions

During development the main considerations were:

1. **Validation-driven API** – using Pydantic models to enforce schema early and convert FastAPI 422 errors into 400 responses.
2. **Decoupling** – the producer merely publishes, never touches the database; the consumer owns persistence, enabling horizontal scaling.
3. **Resilience** – the consumer retries database insertions, logs failures, and gracefully handles malformed JSON without crashing.
4. **Configuration via env vars** – all hostnames, ports, credentials and even the queue name are environment controlled and documented in `.env.example`.
5. **Testing strategy** – containerized integration tests interact with real RabbitMQ and MySQL instances to prove end-to-end functionality.

These decisions keep the system simple yet production‑like and make it easy for additional microservices to plug in later.

---

---

## Author

**Pavan Kumar Goli**
