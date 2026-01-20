# CleanIt Development Environment Setup

This document describes how to set up and use the Docker-based development environment for CleanIt.

## Overview

The development environment uses Docker Compose with:
- **Flask development server** (auto-reload enabled) instead of gunicorn
- **S3 storage** via MinIO (production-like configuration)
- **PostgreSQL database** (same as production)
- **Source code mounting** for live reload during development
- **Development scripts** for easy management

## Quick Start

### 1. Initial Setup

First set the environment variables using the set_env.py script:
```bash
python set_env.py
```

Then set up the development scripts:
```bash
# Make scripts executable
chmod +x bin/*

# Run setup script to make commands globally available
./bin/setup-dev-scripts

# If ~/bin is not in your PATH, add it to your shell profile:
# export PATH="$HOME/bin:$PATH"
# Then: source ~/.bashrc (or restart shell)
```

### 2. Start Development Environment

```bash
# Start all services
cleanit-up

# Or start in detached mode (background)
cleanit-up -d
```

### 3. Access the Application

- **Flask Application**: http://localhost:5000
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)
- **PostgreSQL**: localhost:5432

## Development Commands

### Main Commands

| Command | Description | Example |
|---------|-------------|---------|
| `cleanit-up` | Start development environment | `cleanit-up -d` |
| `cleanit-down` | Stop development environment | `cleanit-down` |
| `cleanit-logs` | View container logs | `cleanit-logs -f web` |
| `cleanit-shell` | Open Flask shell in container | `cleanit-shell` |
| `cleanit-test` | Run tests in container | `cleanit-test -v` |

### Advanced Usage with `cleanit-dev`

The main command `cleanit-dev` supports all operations:

```bash
# Show help
cleanit-dev help

# Start services
cleanit-dev start

# Stop services
cleanit-dev stop

# View logs
cleanit-dev logs

# Run tests
cleanit-dev test tests/test_media_service.py

# Show container status
cleanit-dev status

# Clean up (remove volumes)
cleanit-dev clean
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

### Typical Development Session

```bash
# 1. Start development environment
cleanit-up -d

# 2. Make code changes
# ... edit files ...

# 3. Check logs if needed
cleanit-logs -f web

# 4. Run tests
cleanit-test

# 5. Open Flask shell for debugging
cleanit-shell

# 6. Stop when done
cleanit-down
```

### Running Tests

```bash
# Run all tests
cleanit-test

# Run specific test file
cleanit-test tests/test_media_service.py

# Run with verbose output
cleanit-test -v

# Run specific test function
cleanit-test tests/test_media_service.py::test_upload_media
```

### Debugging

```bash
# Open Flask shell
cleanit-shell

# View application logs
cleanit-logs -f web

# Check container status
cleanit-dev status

# Restart just the web container
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart web
```

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
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
   ```

3. **Database connection issues**
   ```bash
   # Check if PostgreSQL is running
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps postgres
   
   # Restart database
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart postgres
   ```

4. **MinIO not accessible**
   ```bash
   # Check MinIO logs
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs minio
   
   # Wait for MinIO to initialize (takes ~30 seconds on first run)
   ```

### Cleaning Up

```bash
# Stop and remove containers, networks, and volumes
cleanit-dev clean

# Remove all Docker resources (careful!)
docker system prune -a --volumes
```

## Script Details

### Available Scripts in `bin/`

- `cleanit-dev` - Main command with all options
- `cleanit-up` - Start development environment
- `cleanit-down` - Stop development environment  
- `cleanit-logs` - View container logs
- `cleanit-shell` - Open Flask shell
- `cleanit-test` - Run tests
- `setup-dev-scripts` - Setup script for global access

### Making Scripts Globally Available

1. Run the setup script:
   ```bash
   ./bin/setup-dev-scripts
   ```

2. Ensure `~/bin` is in your PATH:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/bin:$PATH"
   
   # Reload shell
   source ~/.bashrc
   ```

3. Verify installation:
   ```bash
   which cleanit-up
   # Should show: /home/yourusername/bin/cleanit-up
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
3. Check the logs: `cleanit-logs`
4. Ensure `.env` file is properly configured