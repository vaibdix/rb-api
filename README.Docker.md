## RB-API Application - Docker Setup

### Prerequisites

- Docker installed on your system
- Docker Compose installed on your system
- MongoDB Atlas account (or MongoDB connection string)

### Project Structure

```
RB-API/
├── database/
│   ├── models.py
│   └── schemas.py
├── documents/
├── static/
│   └── index.html
├── templates/
│   └── index.html
├── configurations.py
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

### Environment Setup

1. Create a `.env` file in the project root:

```env
MONGODB_URL=your_mongodb_connection_string
```

### Docker Commands

#### Build and Run

```bash
# Build and start containers
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

#### Stop Application

```bash
# Stop containers
docker-compose down
```

#### View Logs

```bash
# View logs
docker-compose logs

# Follow logs
docker-compose logs -f
```

#### Container Management

```bash
# List containers
docker-compose ps

# Restart services
docker-compose restart

# Stop services
docker-compose stop

# Start services
docker-compose start
```

### Application Access

Once running, the application is available at:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs