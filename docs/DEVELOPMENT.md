# CleanIt Development Environment Setup

This document describes how to set up and use the Docker-based development environment for CleanIt.

## Overview

The development environment uses Docker Compose with:
- **Flask development server** (auto-reload enabled) instead of gunicorn
- **S3 storage** via MinIO (production-like configuration)
- **PostgreSQL database** (same as production)
- **Source code mounting** for live reload during development
- **Basic utility scripts** for common operations

## Quick Start

### 1. Initial Setup

First set the environment variables using the set_env.py script:
```bash
python set_env.py
```

Then make the utility scripts executable:
```bash
# Make scripts executable
chmod +x bin/*
```

Optionally, use the direnv setup script to add bin/ to your PATH when in the project directory:
```bash
./bin/setup-direnv
```

### 2. Start Development Environment

```bash
# Start all services in detached mode (background)
docker compose up -d

# Or start with rebuild if needed
docker compose up -d --build
```

### 3. Access the Application

- **Flask Application**: http://localhost:5000
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)
- **PostgreSQL**: localhost:5432

## Development Commands

### Main Commands

Use standard Docker Compose commands for most operations:

```bash
# Start services (detached mode)
docker compose up -d

# Start with rebuild
docker compose up -d --build

# Stop services
docker compose down

# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs [service_name]

# Rebuild containers
docker compose build

# Stop and remove volumes
docker compose down -v
```

### Utility Scripts

The `bin/` directory contains basic utility scripts:

```bash
# Open bash shell in a container
./bin/cleanit-bash [container_name]

# View logs for a specific container (last 20 lines)
./bin/cleanit-log [container_name]

# Clean up containers and volumes
./bin/cleanit-clean-volumes

# Restart specific container
./bin/cleanit-restart [container_name]
# Copy files/directories into the flask container
./bin/cleanit-copy <source> [destination]

# Setup direnv to add bin/ to PATH in this project
./bin/setup-direnv
```


## Development Features

### Auto-Reload
The Flask development server automatically reloads when you change:
- Python files in `controllers/`, `routes/`, `services/`, `utils/`
- Template files in `templates/`
- Configuration files

### Source Code Mounting
All source code is mounted into the container, so changes are immediately reflected.

### S3 Storage in Development
Uses MinIO (S3-compatible) for storage, matching production configuration:
- Bucket: `cleanit-media` (configurable via `S3_BUCKET` env var)
- Access: http://localhost:9000 (API), http://localhost:9001 (Console)
- Credentials: admin/minioadmin (default)

### Database
- Uses PostgreSQL (same as production)
- Auto-populated with test data on startup
- Persistent data in Docker volume

## Environment Configuration

### Development Environment Variables
Create a `.env` file in the project root (or copy from `.env.example` if available):

```bash
# Flask Configuration
FLASK_ENV=debug
SECRET_KEY=your-development-secret-key

# Database Configuration
POSTGRES_DB=cleanit
POSTGRES_USER=cleanit_user
POSTGRES_PASSWORD=your-password

# MinIO/S3 Configuration
S3_BUCKET=cleanit-media
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

### Configuration Files
- `docker-compose.yml` - Base configuration (production-ready)
- `docker-compose.dev.yml` - Development overrides (auto-reload, debugging)
- `Dockerfile` - Multi-stage build (development uses builder stage)

## Development Workflow

### Development Philosophy
**Keep the same Docker build for as long as possible** to avoid unnecessary rebuilding. The development workflow prioritizes copying updated files into running containers over rebuilding them. This approach saves time and maintains container state.

### Typical Development Session

```bash
# 1. First time: Build and start environment
docker compose up -d --build

# Subsequent starts: Use existing containers
docker compose up -d

# 2. Make code changes
# ... edit files ...

# 3. Copy updated files into container (instead of rebuilding)
./bin/cleanit-copy ./controllers /app/controllers
./bin/cleanit-copy ./templates /app/templates
# Or copy specific changed files

# 4. Flask auto-reload will detect changes and restart
# Alternatively rest out the container if needed: cleanit-restart web
# 5. View logs if needed
docker compose logs -f

# 6. Stop when done
docker compose down
```

### When to Rebuild vs Copy
- **Copy files**: When changing application code (Python, templates, static files)
- **Rebuild containers**: When changing dependencies (requirements.txt, Dockerfile, system packages)

### Running Tests

Currently tests have to be run outside of the docker configuration using pytest.

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 5000
   sudo lsof -i :5000
   
   # Or use different port in docker-compose.dev.yml
   ```

2. **Docker build fails**
   ```bash
   # Clean build
   docker compose build --no-cache
   ```

3. **Database connection issues**
   ```bash
   # Check if PostgreSQL is running
   docker compose ps postgres
   
   # Restart database
   docker compose restart postgres
   ```

4. **MinIO not accessible**
   ```bash
   # Check MinIO logs
   docker compose logs minio
   
   # Wait for MinIO to initialize (takes ~30 seconds on first run)
   ```

### Cleaning Up

```bash
# Stop and remove containers, networks, and volumes
docker compose down -v

# Or use the utility script
./bin/cleanit-clean-volumes

# Remove all Docker resources (careful!)
docker system prune -a --volumes
```

## Script Details

### Available Scripts in `bin/`

- `cleanit-bash` - Open bash shell in a container
- `cleanit-log` - View logs for a specific container (last 20 lines)
- `cleanit-clean-volumes` - Stop containers and remove volumes
- `cleanit-copy` - Copy files/directories into the flask container
- `setup-direnv` - Setup direnv to add bin/ to PATH in this project

### Making Scripts Accessible

Option 1: Use direnv (recommended)
```bash
./bin/setup-direnv
# This adds bin/ to your PATH when in the project directory
```

Option 2: Add to PATH manually
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PWD/bin:$PATH"

# Reload shell
source ~/.bashrc
```

Option 3: Use with ./ prefix
```bash
# Simply run scripts with ./ prefix
./bin/cleanit-bash flask
./bin/cleanit-copy ./static/js /app/static/js
```

## Production vs Development

| Aspect | Production | Development |
|--------|------------|-------------|
| Server | Gunicorn (multi-worker) | Flask dev server (auto-reload) |
| Storage | S3 (cloud) | MinIO (local S3-compatible) |
| Debug | Disabled | Enabled |
| Database | PostgreSQL | PostgreSQL (same) |
| Ports | 5000 only | 5000 + 5678 (debug) |

## Next Steps

1. **Customize environment**: Edit `.env` for your specific needs
2. **Add test data**: Modify `utils/populate_database.py` for development data
3. **Configure IDE**: Set up remote debugging on port 5678 if needed
4. **Set up CI/CD**: Use the same Docker configuration for testing

## Support

For issues with the development environment:
1. Check Docker and Docker Compose are installed and running
2. Verify ports 5000, 5432, 9000, 9001 are available
3. Check the logs: `docker compose logs` or `./bin/cleanit-log [service]`
4. Ensure `.env` file is properly configured