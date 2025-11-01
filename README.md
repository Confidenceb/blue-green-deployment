# Blue/Green Deployment with Nginx

This project demonstrates a **Blue/Green deployment** setup for a Node.js application using **pre-built Docker images** and **Nginx** as a reverse proxy with auto-failover.

Traffic is routed to the **active pool (Blue by default)**, and if the active pool fails, Nginx automatically switches to the backup (Green) with zero failed client requests.

## Features

- Blue/Green deployment with pre-built Node.js images
- Nginx reverse proxy with upstream failover
- Automatic retry on 5xx or timeout errors
- Maintains application headers (`X-App-Pool`, `X-Release-Id`)
- Chaos endpoints to simulate downtime (`/chaos/start` and `/chaos/stop`)
- Fully parameterized using a `.env` file

## Prerequisites

- Docker and Docker Compose installed
- Linux, macOS, or Windows (with WSL recommended for Windows)
- Access to EC2 (optional, if deploying to AWS)

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/<your-username>/blue-green-deployment.git
cd blue-green-deployment
```

2. **Create `.env` file**
   Copy `.env.example` and update variables as needed:

```bash
cp .env.example .env
```

Variables include:

```text
BLUE_IMAGE=yimikaade/wonderful:devops-stage-two
GREEN_IMAGE=yimikaade/wonderful:devops-stage-two
ACTIVE_POOL=blue
RELEASE_ID_BLUE=blue-v1
RELEASE_ID_GREEN=green-v1
PORT=3000
```

3. **Start services with Docker Compose**

```bash
docker-compose up -d
```

- Nginx will be available at `http://localhost:8080`
- Blue direct endpoint: `http://localhost:8081`
- Green direct endpoint: `http://localhost:8082`

## Testing the Deployment

### Check Active Pool

```bash
curl http://localhost:8080/version -i
```

Expected headers:

```
X-App-Pool: blue
X-Release-Id: blue-v1
```

### Simulate Chaos (Failover)

**Trigger downtime on Blue:**

```bash
curl -X POST http://localhost:8081/chaos/start?mode=error
```

**Check Nginx endpoint:**

```bash
curl http://localhost:8080/version -i
```

Expected headers:

```
X-App-Pool: green
X-Release-Id: green-v1
```

**Restore Blue:**

```bash
curl -X POST http://localhost:8081/chaos/stop
```

Traffic should automatically revert to Blue.

## Notes

- The Docker images are pre-built; no application code changes are required.
- Nginx is configured via a template (`nginx.conf.template`) that uses environment variables for the active pool.
- Timeouts and retries are configured in Nginx to ensure failover is fast and reliable.

## Cleanup

To stop all containers:

```bash
docker-compose down
```

# Stage 3 - Observability and Alerts (Blue-Green Deployment)

## Overview

This project extends the Stage 2 Blue/Green setup by adding observability and real-time Slack alerts.

## Components

- **Nginx**: Reverse proxy and load balancer.
- **Blue/Green Apps**: Serve traffic via Nginx upstream.
- **Log Watcher (Python)**: Monitors Nginx logs and sends Slack alerts on high error rates.

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env`:

```bash
   cp .env.example .env
```

3. Update `.env` with your Slack webhook URL
4. Run: `docker-compose up -d --build`

```

### Alternative: If you want to keep the commits as-is

You can allow the secret on GitHub by clicking the link in the error message:
```

https://github.com/Confidenceb/blue-green-deployment/security/secret-scanning/unblock-secret/34t0bvGqkISlDKgvV7gJOtLiuJk
