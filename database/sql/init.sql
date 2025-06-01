-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    role_name VARCHAR(100) NOT NULL
);

INSERT INTO roles (id, key, role_name) VALUES
(1, 'PP_USER', 'PP User'),
(2, 'PP_ADMIN', 'PP Admin')
ON CONFLICT (key) DO NOTHING;

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'view', 'add', 'edit', 'delete'
    name VARCHAR(100) NOT NULL
);

INSERT INTO permissions (id, key, name) VALUES
(1, 'view', 'View'),
(2, 'add', 'Add'),
(3, 'edit', 'Edit'),
(4, 'delete', 'Delete')
ON CONFLICT (key) DO NOTHING;


-- Modules table
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'M_INSURANCE_CABINET', 'M_POLICY_QUOTES', 'M_RATING_RESULT', 'M_AI_ASSISTANT'
    name VARCHAR(100) NOT NULL,
    url VARCHAR(255),
    priority INTEGER DEFAULT 0
);


INSERT INTO modules (id, key, name, url, priority) VALUES
(1, 'M_INSURANCE_CABINET', 'Insurance Cabinet', '/insurance-cabinet', 1),
(2, 'M_POLICY_QUOTES', 'Policy Quotes', '/policy-quotes', 2),
(3, 'M_RATING_RESULT', 'Rating Result', '/rating-result', 3),
(4, 'M_AI_ASSISTANT', 'AI Assistant', '/ai-assistant', 4)
ON CONFLICT (key) DO NOTHING;


-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_no VARCHAR(20),
    picture TEXT,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Role to Module mapping
CREATE TABLE IF NOT EXISTS role_modules (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    UNIQUE(role_id, module_id)
);

-- Role_Module to Permission mapping
CREATE TABLE IF NOT EXISTS role_module_permissions (
    id SERIAL PRIMARY KEY,
    role_module_id INTEGER NOT NULL REFERENCES role_modules(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(role_module_id, permission_id)
);

-- User Providers (for social login)
CREATE TABLE IF NOT EXISTS user_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- e.g., 'google', 'apple'
    provider_sub VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- Email verifications table (outside user table)
CREATE TABLE IF NOT EXISTS email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    verification_token VARCHAR(255) NOT NULL UNIQUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
