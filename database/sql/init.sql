-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone_no VARCHAR(20),
    is_verified BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

create table if not exists Roles (
    id int primary key auto_increment,
    role_key varchar(50) not null unique,
    role_name varchar(50) not null unique
);

-- Insert default role only once 
-- USER & ADMIN
INSERT IGNORE INTO Roles (id, role_key, role_name)VALUES (1, 'PP_ADMIN', 'PP Admin'), (2, 'PP_USER', 'PP User');


