# User Roles and Permissions

This document outlines the user role system in Jamso AI Server.

## Role Hierarchy

The system implements a hierarchical role-based access control system with the following roles:

1. **Admin** - Full system access and user management
2. **User** - Regular user with trading access
3. **Viewer** - Read-only access to dashboard and data

## Role Capabilities

### Admin Role

Administrators have complete access to the system, including:

- User management (create, view, update, delete users)
- System configuration and settings
- API key management
- Full trading capabilities
- Access to all dashboard features
- System monitoring and logs

### User Role

Regular users have standard trading access:

- View and manage trading accounts
- Execute trades
- Configure personal trading settings
- View trading history and performance
- Basic account management

### Viewer Role

Viewers have read-only access:

- View dashboard statistics
- View trading history
- View performance metrics
- No ability to execute trades or change settings

## Permission Matrix

| Feature                   | Admin | User | Viewer |
|---------------------------|-------|------|--------|
| View Dashboard            | ✓     | ✓    | ✓      |
| View Trading History      | ✓     | ✓    | ✓      |
| Execute Trades            | ✓     | ✓    | ✗      |
| Manage Trading Accounts   | ✓     | ✓    | ✗      |
| Configure Webhooks        | ✓     | ✓    | ✗      |
| Manage API Keys           | ✓     | ✓    | ✗      |
| View System Logs          | ✓     | ✗    | ✗      |
| Access User Management    | ✓     | ✗    | ✗      |
| Change System Settings    | ✓     | ✗    | ✗      |

## Role Assignment

Roles are assigned during user creation or can be modified by administrators through the user management interface in the dashboard.

## Default User

By default, the system creates an admin user during initial setup with the username "admin". This user has full administrative privileges, and the password should be changed immediately after installation.
