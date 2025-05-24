# Mobile Alerts Integration for Capital.com API Optimization

## Overview

The Mobile Alerts system provides real-time notifications for critical events in the Capital.com API optimization process. This feature enhances the monitoring capabilities of the Jamso-AI-Engine by delivering timely notifications about performance degradation, optimization completion, and system status.

## Supported Notification Methods

The system supports multiple notification channels to ensure alerts reach users regardless of their preferred communication method:

1. **Email notifications**: Sends detailed HTML emails with performance metrics and charts
2. **SMS notifications**: Delivers concise text messages for urgent alerts (via email-to-SMS gateways)
3. **Push notifications**: Sends notifications to mobile devices using OneSignal or Firebase
4. **Webhook integrations**: Enables custom notification systems through webhooks

## Components

The Mobile Alerts system consists of these key components:

- `mobile_alerts.py`: Core module that handles alert generation and delivery
- Integration with `scheduled_optimization.py` for automated notifications
- Configuration in `.env` file for alert settings

## Configuration

All mobile alert settings are configured in the `.env` file:

```properties
# Email settings for alerts
EMAIL_FROM=your.email@gmail.com
EMAIL_TO=recipient@example.com
EMAIL_PASSWORD=your_email_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Mobile Alert Settings
MOBILE_ALERTS_EMAIL_ENABLED=true
MOBILE_ALERTS_SMS_ENABLED=false
MOBILE_ALERTS_PUSH_ENABLED=false
MOBILE_ALERTS_WEBHOOK_ENABLED=false
MOBILE_ALERTS_MIN_LEVEL=warning

# SMS Gateway settings (if using SMS alerts)
SMS_GATEWAY=txt.att.net
SMS_NUMBER=1234567890

# Push notification settings (if using push notifications)
PUSH_SERVICE=onesignal
PUSH_API_KEY=your_api_key
PUSH_APP_ID=your_app_id

# Webhook settings (if using webhook alerts)
WEBHOOK_ALERT_URL=https://your-webhook-url.com/hook
WEBHOOK_ALERT_HEADERS={"Content-Type": "application/json", "Authorization": "Bearer your_token"}
```

## Alert Types

The Mobile Alerts system categorizes alerts into three levels:

1. **Info (Low priority)**: Routine notifications like optimization completion with good results
2. **Warning (Medium priority)**: Situations requiring attention like minor performance degradation
3. **Critical (High priority)**: Urgent problems like severe performance degradation or system failures

## Alert Content

Each alert contains:

1. **Title**: Brief description of the event
2. **Message**: Detailed information about what happened
3. **Level**: Info, warning, or critical
4. **Timestamp**: When the event occurred
5. **Additional Data**: Performance metrics, parameters, or other relevant information

## Integration with Optimization Process

The Mobile Alerts system is integrated into the optimization process to provide notifications for:

1. **Optimization Scheduler Start/Stop**: Alerts when the scheduled optimization process starts or stops
2. **Optimization Completion**: Notifications about completed optimization runs with performance metrics
3. **Parameter Degradation**: Critical alerts when strategy performance degrades significantly
4. **System Errors**: Notifications about system errors or failures

## Rate Limiting

To prevent alert fatigue, the Mobile Alerts system implements rate limiting:

- Info alerts: Maximum 10 per hour
- Warning alerts: Maximum 5 per hour
- Critical alerts: Maximum 3 per hour

## Usage Examples

### Sending a Basic Alert

```python
from src.AI.mobile_alerts import MobileAlertManager

# Initialize alert manager
alert_manager = MobileAlertManager()

# Send an informational alert
alert_manager.send_alert(
    "Optimization Complete",
    "BTCUSD optimization completed successfully with 15.2% return",
    level="info"
)
```

### Sending a Critical Alert with Additional Data

```python
alert_manager.send_alert(
    "Severe Performance Degradation",
    "BTCUSD strategy performance decreased by 25%",
    level="critical",
    data={
        "symbol": "BTCUSD",
        "timeframe": "HOUR",
        "previous_return": 12.5,
        "current_return": 9.3,
        "sharpe_ratio": 1.2,
        "drawdown": 15.8
    }
)
```

## Testing

A test script is provided to verify mobile alert functionality:

```bash
./Tools/test_mobile_alerts.sh
```

This script tests the configuration, basic alert functionality, and integration with the scheduled optimization process.

## Command Line Options

The scheduled optimization script now accepts mobile alert options:

```bash
python src/AI/scheduled_optimization.py --mobile-alerts --alert-level warning
```

Options:
- `--mobile-alerts`: Enable mobile alerts
- `--alert-level`: Minimum alert level to send (info, warning, critical)

## Security Considerations

1. **Email Credentials**: Store email credentials securely and use app-specific passwords when possible
2. **API Keys**: Keep API keys for push notification services secure
3. **Webhook URLs**: Use authentication for webhook endpoints
4. **Environment Variables**: Don't commit .env file with credentials to version control

## Troubleshooting

Common issues and their solutions:

1. **No alerts received via email**:
   - Check SMTP server settings
   - Verify email credentials
   - Enable "Less secure app access" or use app-specific password for Gmail

2. **SMS alerts not working**:
   - Verify carrier SMS gateway format
   - Ensure email-to-SMS gateway is correctly configured

3. **Push notifications not delivered**:
   - Verify API keys for OneSignal/Firebase
   - Check device subscription status
   - Confirm app ID is correct

4. **Rate limiting preventing alerts**:
   - Check logs for rate limit messages
   - Consider adjusting rate limits for your use case

## Next Steps

Future enhancements planned for the Mobile Alerts system:

1. **Custom Notification Templates**: Allow customization of alert formats
2. **Alert Preferences UI**: Web interface for configuring alert preferences
3. **Alert History Dashboard**: Visualization of past alerts and trends
4. **Mobile App Integration**: Direct integration with Jamso-AI-Engine mobile app
5. **Advanced Filtering**: More sophisticated rules for alert delivery
