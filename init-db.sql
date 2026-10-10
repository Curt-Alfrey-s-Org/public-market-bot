-- PostgreSQL initialization script for market-pie5-bot
-- Creates schemas and enables required extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas for organized table management
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS trading;

-- Set search path to include both schemas
ALTER DATABASE marketbot SET search_path TO auth, trading, public;

-- Create indexes for performance (tables will be created by Alembic)
-- Placeholder: Alembic migrations will handle table creation

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON SCHEMA auth TO marketbot_user;
GRANT ALL PRIVILEGES ON SCHEMA trading TO marketbot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO marketbot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA trading TO marketbot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO marketbot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA trading TO marketbot_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON TABLES TO marketbot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA trading GRANT ALL ON TABLES TO marketbot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON SEQUENCES TO marketbot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA trading GRANT ALL ON SEQUENCES TO marketbot_user;
