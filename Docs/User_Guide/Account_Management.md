# Account Management

This guide explains how to manage trading accounts in the Jamso AI Server.

## Overview

The Jamso AI Server supports both demo and live trading accounts with Capital.com. The account management features allow you to:

- Switch between demo and live environments
- Select specific trading accounts
- View account details and balances
- Configure account-specific settings

## Accessing Account Management

You can access account management through:
1. The dashboard sidebar menu
2. The account selection dropdown in the header
3. The dedicated account management page

## Account Types

### Demo Accounts

Demo accounts are used for testing and development. They:
- Use virtual funds
- Connect to the Capital.com demo server (`https://demo-api-capital.backend-capital.com`)
- Appear with a "Demo" badge in the interface
- Have no real financial risk

### Live Accounts

Live accounts use real funds for trading. They:
- Connect to the Capital.com live server (`https://api-capital.backend-capital.com`)
- Involve real financial transactions
- Appear with a "Live" badge in the interface
- Require additional verification and security measures

## Switching Between Accounts

To switch between accounts:

1. Navigate to the Account Selection page
2. Choose between Demo or Live environment
3. Select the specific account from the list
4. Click "Activate Account"

The system will store your selection in the database, and all trading operations will use the selected account.

## Account Details

The account details page displays:
- Account ID
- Account name
- Current balance
- Available margin
- Currency
- Account type
- Recent activity

## Security Considerations

When working with live accounts:
- Additional confirmation dialogs appear for sensitive operations
- Live accounts are highlighted in red for visual distinction
- Automatic timeout occurs after periods of inactivity
- API keys are stored encrypted in the database

## API Keys

Managing Capital.com API keys:
1. Navigate to the API Keys section
2. Enter your Capital.com credentials
3. The system will generate and store API keys securely
4. Different keys are maintained for demo and live environments

## Troubleshooting

Common account issues:
- **Authentication Failures**: Check that your API credentials are correct
- **Account Not Found**: Ensure the account is active in Capital.com
- **Switching Errors**: The database may require permissions adjustment
- **Balance Discrepancies**: Refresh account data from Capital.com
