# Auth Service

## Overview
Authentication and authorization service for the Meeting Minutes application.

## Architecture
- Port: 8000 (internal), 8004 (external)
- Database: MongoDB
- JWT Authentication

## Data Models

### User
- email (required, unique)
- password_hash (required)
- name (required)
- created_at, updated_at

## API Endpoints

### Authentication
- `POST /auth/register`
  - Registers new user
  - Requires: email, password, name

- `POST /auth/login`
  - Authenticates user
  - Requires: username (email), password
  - Returns: JWT token

- `GET /auth/me`
  - Gets current user info
  - Requires: Bearer token

### Health Check
- `GET /health`
  - Checks service and database health

## Configuration
- MONGODB_URI: MongoDB connection string
- JWT_SECRET: Secret key for JWT signing 