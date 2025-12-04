# 🚀 QuantAgent Deployment Guide

This guide covers different deployment options for QuantAgent.

## Table of Contents
- [Docker Deployment (Recommended)](#docker-deployment-recommended)
- [Local Development](#local-development)
- [Cloud Deployment](#cloud-deployment)
- [Environment Variables](#environment-variables)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

---

## Docker Deployment (Recommended)

The easiest way to deploy QuantAgent is using Docker and Docker Compose.

### Prerequisites
- Docker (version 20.10+)
- Docker Compose (version 2.0+)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Y-Research-SBU/QuantAgent.git
   cd QuantAgent
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your API keys
   ```

3. **Deploy with one command**
   ```bash
   ./deploy.sh
   ```

   The application will be available at `http://localhost:5000`

### Manual Docker Commands

If you prefer manual control:

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Docker Configuration

The `docker-compose.yml` file includes:
- **Port mapping**: 5000:5000
- **Volume mounts**:
  - `./data` for persistent charts and analysis
  - `./benchmark` for benchmark datasets (read-only)
- **Health checks**: Automatic container health monitoring
- **Restart policy**: Container restarts automatically on failure

---

## Local Development

For local development without Docker:

### Prerequisites
- Python 3.11
- pip or conda

### Setup

1. **Create virtual environment**
   ```bash
   # Using conda (recommended)
   conda create -n quantagents python=3.11
   conda activate quantagents

   # Or using venv
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install TA-Lib**
   ```bash
   # On macOS
   brew install ta-lib

   # On Ubuntu/Debian
   sudo apt-get install ta-lib

   # On Windows - download from:
   # https://github.com/ta-lib/ta-lib-python

   # Or use conda
   conda install -c conda-forge ta-lib
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export OPENAI_API_KEY="your_key_here"
   export ANTHROPIC_API_KEY="your_key_here"  # Optional
   export DASHSCOPE_API_KEY="your_key_here"  # Optional
   ```

5. **Run the application**
   ```bash
   python web_interface.py
   ```

   Access at `http://127.0.0.1:5000`

---

## Cloud Deployment

### Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click the "Deploy on Railway" button
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY` (optional)
   - `DASHSCOPE_API_KEY` (optional)
   - `HOST=0.0.0.0`
   - `PORT=5000`
4. Deploy!

### Heroku

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   ```

2. **Create Heroku app**
   ```bash
   heroku create your-quantagent-app
   ```

3. **Add buildpacks**
   ```bash
   heroku buildpacks:add --index 1 https://github.com/numrut/heroku-buildpack-ta-lib
   heroku buildpacks:add --index 2 heroku/python
   ```

4. **Set environment variables**
   ```bash
   heroku config:set OPENAI_API_KEY="your_key"
   heroku config:set HOST="0.0.0.0"
   heroku config:set PORT="5000"
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

### AWS EC2

1. **Launch EC2 instance** (Ubuntu 22.04 LTS recommended)

2. **Install Docker**
   ```bash
   sudo apt-get update
   sudo apt-get install docker.io docker-compose
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Clone and deploy**
   ```bash
   git clone https://github.com/Y-Research-SBU/QuantAgent.git
   cd QuantAgent
   sudo ./deploy.sh
   ```

4. **Configure security group**
   - Allow inbound traffic on port 5000
   - Or use nginx as reverse proxy on port 80/443

### Digital Ocean

Similar to AWS EC2, use Docker deployment on a Droplet.

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | `sk-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | - |
| `DASHSCOPE_API_KEY` | DashScope API key for Qwen | - |
| `HOST` | Server host binding | `127.0.0.1` |
| `PORT` | Server port | `5000` |
| `FLASK_ENV` | Flask environment | `production` |
| `FLASK_DEBUG` | Enable debug mode | `0` |

### Setting Environment Variables

**In Docker:**
```bash
# Edit .env file
nano .env

# Or set in docker-compose.yml
```

**In Shell:**
```bash
export OPENAI_API_KEY="your_key"
```

**In Python:**
```python
import os
os.environ["OPENAI_API_KEY"] = "your_key"
```

---

## Health Checks

QuantAgent includes a health check endpoint for monitoring:

```bash
# Check application health
curl http://localhost:5000/health

# Response (healthy):
{
  "status": "healthy",
  "service": "QuantAgent",
  "timestamp": "2025-12-04T10:30:00"
}

# Response (unhealthy):
{
  "status": "unhealthy",
  "error": "error message"
}
```

### Docker Health Check

The Docker container includes automatic health checks:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start period**: 40 seconds

View health status:
```bash
docker-compose ps
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs -f

# Rebuild image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### API Key Issues

```bash
# Verify API key is set
docker-compose exec quantagent env | grep API_KEY

# Update API key
# Edit .env file, then restart
docker-compose restart
```

### TA-Lib Installation Failed

```bash
# In Dockerfile, the TA-Lib C library is installed from source
# If build fails, check Docker build logs:
docker-compose build 2>&1 | grep -A 20 "ta-lib"
```

### Port Already in Use

```bash
# Change port in .env
PORT=5001

# Or kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

### Memory Issues

For large datasets, increase Docker memory:

```bash
# Edit docker-compose.yml, add under 'quantagent' service:
deploy:
  resources:
    limits:
      memory: 2G
```

### Performance Optimization

**For production:**

1. **Use production WSGI server** (add to requirements.txt):
   ```bash
   pip install gunicorn
   ```

2. **Update Dockerfile CMD**:
   ```dockerfile
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_interface:app"]
   ```

3. **Enable caching** for frequently accessed data

4. **Use nginx reverse proxy** for SSL and load balancing

---

## Monitoring

### Application Logs

```bash
# View live logs
./logs.sh

# Or with Docker Compose
docker-compose logs -f quantagent

# View last 100 lines
docker-compose logs --tail=100 quantagent
```

### Resource Usage

```bash
# Container stats
docker stats quantagent-app

# Disk usage
docker-compose exec quantagent du -sh /app/data
```

---

## Scaling

### Horizontal Scaling

For multiple instances:

1. **Use load balancer** (nginx, HAProxy)
2. **Share state** via Redis or database
3. **Scale containers**:
   ```bash
   docker-compose up -d --scale quantagent=3
   ```

### Vertical Scaling

Increase container resources in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

---

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use secrets management** - AWS Secrets Manager, HashiCorp Vault
3. **Enable HTTPS** - Use nginx with Let's Encrypt
4. **Limit API access** - Add authentication middleware
5. **Regular updates** - Keep dependencies updated
6. **Monitor logs** - Set up centralized logging

---

## Support

For deployment issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review container logs: `./logs.sh`
3. Join [Discord Community](https://discord.gg/t9nQ6VXQ)
4. Open an issue on [GitHub](https://github.com/Y-Research-SBU/QuantAgent/issues)

---

## License

This project is licensed under the MIT License.
