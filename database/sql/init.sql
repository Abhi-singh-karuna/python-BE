-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    -- phone_no VARCHAR(20),
    phone_no INTEGER,
    is_verified BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_key VARCHAR(50) NOT NULL UNIQUE,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Insert default roles only if they don't exist
INSERT INTO roles (role_key, role_name)
SELECT 'PP_ADMIN', 'PP Admin'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE role_key = 'PP_ADMIN');

INSERT INTO roles (role_key, role_name)
SELECT 'PP_USER', 'PP User'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE role_key = 'PP_USER');


