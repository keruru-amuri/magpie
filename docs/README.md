# MAGPIE Platform Documentation

This directory contains documentation for the MAGPIE platform.

## Contents

- [Architecture Overview](../architecture.md)
- [API Documentation](#api-documentation)
- [Development Guide](#development-guide)
- [Deployment Guide](#deployment-guide)

## API Documentation

The API documentation is automatically generated using FastAPI's built-in Swagger UI. When the application is running, you can access it at:

```
http://localhost:8000/docs
```

## Development Guide

### Setting Up Development Environment

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file based on `.env.example`
4. Run the application: `uvicorn app.main:app --reload`

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. To check your code:

```bash
flake8 app tests
```

## Deployment Guide

### Docker Deployment

```bash
docker-compose up -d
```

### Azure Deployment

Detailed instructions for deploying to Azure will be added in the future.
