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
- FastAPI API service
- Receives user events
- Publishes events to RabbitMQ

### RabbitMQ
- Message queue broker
- Decouples producer and consumer

### Consumer Service
- Consumes events from queue
- Stores them in MySQL

### MySQL Database
- Stores processed events

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

Use Swagger UI or curl:

```
bash
curl -X POST http://localhost:8000/api/v1/events/track \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "1",
    "event_type": "login",
    "timestamp": "2026-02-17 15:10:00",
    "metadata": {"ip":"127.0.0.1"}
  }'
```

**Expected response:** `202 Accepted`

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
SELECT * FROM events;
```

---

## Running Tests

### Producer tests

```
bash
docker-compose exec producer-service pytest
```

### Consumer tests

```
bash
docker-compose exec consumer-service pytest tests/consumer
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

- [ ] Authentication for API
- [ ] Event analytics service
- [ ] Dashboard visualization
- [ ] Dead-letter queues
- [ ] Monitoring & logging

---

## Author

**Pavan Kumar Goli**
