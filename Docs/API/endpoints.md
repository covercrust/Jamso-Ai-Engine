# Jamso AI Server API Documentation

This document provides detailed information about the API endpoints available in the Jamso AI Server application.

## Authentication

Most API endpoints require authentication using the `X-Trading-Token` header.

Example:
```
X-Trading-Token: your_webhook_token_here
```

## Endpoints

### Webhook Endpoint

**URL**: `/webhook`  
**Method**: `POST`  
**Auth Required**: Yes  
**Content-Type**: `application/json`

Handles incoming webhook requests from TradingView or other signal sources.

#### Request Body

```json
{
  "order_id": "unique_order_id",
  "ticker": "AAPL",
  "order_action": "BUY",
  "position_size": 1.0,
  "price": 150.0,
  "stop_loss": 145.0,
  "take_profit": 160.0,
  "trailing_stop": false,
  "hedging_enabled": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| order_id | string | Yes | Unique identifier for the order |
| ticker | string | Yes | Trading instrument symbol |
| order_action | string | Yes | Trade direction (BUY, SELL, CLOSE_BUY, CLOSE_SELL) |
| position_size | number | Yes | Size of the position to open |
| price | number | No | Current price at time of signal (optional) |
| stop_loss | number | No | Stop loss level |
| take_profit | number | No | Take profit level |
| trailing_stop | boolean | No | Whether to use trailing stop |
| trailing_step_percent | number | No | Percentage for trailing stop step |
| hedging_enabled | boolean | No | Whether hedging is enabled |

#### Success Response

**Code**: `200 OK`

```json
{
  "status": "success",
  "order_id": "unique_order_id",
  "deal_reference": "capital_com_deal_reference",
  "trade_details": {
    "ticker": "AAPL",
    "action": "BUY",
    "size": 1.0
  }
}
```

#### Error Response

**Code**: `400 BAD REQUEST` or `500 INTERNAL SERVER ERROR`

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Error message description"
}
```

Common error codes:
- `MISSING_FIELDS`: Required fields are missing
- `JSON_PARSE_ERROR`: Invalid JSON format
- `NO_DATA`: No data received
- `EXECUTION_ERROR`: Error during trade execution

---

### TradingView Webhook Endpoint

**URL**: `/webhook/tradingview`  
**Method**: `POST`  
**Auth Required**: Yes  
**Content-Type**: `application/json`

Specific endpoint for TradingView signals with database integration.

#### Request Body

Same format as the main webhook endpoint.

#### Success Response

**Code**: `200 OK`

```json
{
  "status": "success",
  "signal_id": 123,
  "position_id": 456,
  "deal_reference": "capital_com_deal_reference",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

#### Error Response

Same format as the main webhook endpoint.

---

### Close Position Endpoint

**URL**: `/close_position`  
**Method**: `POST`  
**Auth Required**: No (consider adding authentication in future updates)  
**Content-Type**: `application/json`

Handles requests to close positions on Capital.com.

#### Request Body

```json
{
  "order_id": "unique_order_id",
  "size": 1.0
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| order_id | string | Yes | Original order ID of the position to close |
| size | number | No | Size of the position to close (defaults to entire position) |

#### Success Response

**Code**: `200 OK`

```json
{
  "status": "success",
  "deal_id": "original_deal_id",
  "close_deal_reference": "close_deal_reference",
  "response": {
    // Full response from Capital.com API
  }
}
```

#### Error Response

**Code**: `400 BAD REQUEST` or `500 INTERNAL SERVER ERROR`

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Error message description"
}
```

Common error codes:
- `MISSING_ORDER_ID`: Order ID is required
- `INVALID_SIZE`: Size must be greater than 0
- `DEAL_ID_NOT_FOUND`: No deal ID found for the given order ID
- `POSITION_NOT_FOUND`: No position found for the given deal ID

---

### Dashboard API Endpoints

#### Get Signals Data

**URL**: `/dashboard/api/signals`  
**Method**: `GET`  
**Auth Required**: No (consider adding authentication in future updates)

Retrieves trading signals data for the dashboard.

#### Success Response

**Code**: `200 OK`

```json
[
  {
    "id": 1,
    "timestamp": "2023-01-01T12:00:00Z",
    "order_id": "unique_order_id",
    "deal_id": "capital_com_deal_id",
    "signal_data": "{...}",
    "status": "executed",
    "error": null,
    "position_status": "open",
    "trade_action": "BUY",
    "trade_direction": "LONG",
    "position_size": 1.0,
    "hedging_enabled": false
  },
  // More signal records...
]
```

#### Error Response

**Code**: `500 INTERNAL SERVER ERROR`

```json
{
  "status": "error",
  "code": "API_ERROR",
  "message": "Error message description"
}
```

---

#### Get Positions Data

**URL**: `/dashboard/api/positions`  
**Method**: `GET`  
**Auth Required**: No (consider adding authentication in future updates)

Retrieves current positions data from Capital.com for the dashboard.

#### Success Response

**Code**: `200 OK`

```json
[
  {
    "position": {
      "dealId": "capital_com_deal_id",
      "epic": "AAPL",
      "direction": "BUY",
      "size": 1.0,
      "profit": 100.0,
      "status": "OPEN",
      // Additional position details...
    }
  },
  // More positions...
]
```

#### Error Response

**Code**: `500 INTERNAL SERVER ERROR`

```json
{
  "status": "error",
  "code": "API_ERROR",
  "message": "Error message description"
}
```

## Error Codes

The API uses standardized error codes across all endpoints:

| Error Code | Description |
|------------|-------------|
| JSON_PARSE_ERROR | Invalid JSON format in request |
| NO_DATA | No data received in request |
| MISSING_FIELDS | Required fields are missing |
| UNAUTHORIZED | Authentication required or invalid token |
| VALIDATION_ERROR | Input validation failed |
| API_ERROR | Error from Capital.com API |
| EXECUTION_ERROR | Error during trade execution |
| POSITION_NOT_FOUND | Position not found |
| DEAL_ID_NOT_FOUND | Deal ID not found |
| INVALID_SIZE | Invalid position size |
| INTERNAL_ERROR | Unexpected server error |
| CONNECTION_ERROR | Connection issue with external service |
| TIMEOUT_ERROR | Request timed out |

## Rate Limits

There are currently no explicit rate limits implemented for the API endpoints, but excessive requests may be throttled in the future.