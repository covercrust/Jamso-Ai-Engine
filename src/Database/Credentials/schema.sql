-- Table for storing credentials
CREATE TABLE credentials (
    id INT PRIMARY KEY IDENTITY(1,1),
    service_name NVARCHAR(255) NOT NULL,
    credential_key NVARCHAR(255) NOT NULL,
    credential_value NVARCHAR(MAX) NOT NULL,
    is_encrypted BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- Table for role-based access control
CREATE TABLE roles (
    id INT PRIMARY KEY IDENTITY(1,1),
    role_name NVARCHAR(255) NOT NULL UNIQUE
);

-- Table for users
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(255) NOT NULL UNIQUE,
    email NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    CONSTRAINT FK_user_roles_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT FK_user_roles_roles FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT PK_user_roles PRIMARY KEY (user_id, role_id)
);

-- Table for audit logs
CREATE TABLE audit_logs (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    action NVARCHAR(255) NOT NULL,
    timestamp DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_audit_logs_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);