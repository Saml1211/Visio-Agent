# Integration Guide

## Overview

This guide explains how to integrate the LLD Automation Project into your existing systems and workflows. It covers authentication, API usage, webhook integration, and best practices for deployment.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Integration](#api-integration)
4. [Webhook Integration](#webhook-integration)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- API Key (obtain from system administrator)
- HTTPS endpoint for webhook callbacks
- Python 3.8+ or Node.js 14+ for client libraries
- Network access to API endpoints

### Installation

#### Python
```bash
pip install lld-automation-client
```

#### Node.js
```bash
npm install lld-automation-client
```

## Authentication

### API Key Authentication

1. **Request API Key**
```bash
curl -X POST https://api.lldautomation.com/v1/auth/request-key \
  -H "Content-Type: application/json" \
  -d '{"email": "user@company.com", "purpose": "integration"}'
```

2. **Use API Key in Requests**
```python
from lld_automation import Client

client = Client(api_key="your-api-key")
```

### JWT Authentication

1. **Obtain JWT Token**
```python
token = client.auth.get_token()
```

2. **Refresh Token**
```python
new_token = client.auth.refresh_token(refresh_token)
```

## API Integration

### Basic Integration

```python
from lld_automation import Client

# Initialize client
client = Client(api_key="your-api-key")

# Validate diagram
result = client.validate_diagram("path/to/diagram.vsdx")

# Generate diagram
diagram = client.generate_diagram(
    template="network_diagram",
    components=[{"type": "router", "name": "Core Router"}]
)
```

### Advanced Integration

```python
from lld_automation import Client, ValidationRules

# Custom validation rules
rules = ValidationRules(
    check_colors=True,
    check_text=True,
    check_spacing=True,
    strict_mode=True
)

# Initialize client with custom configuration
client = Client(
    api_key="your-api-key",
    base_url="https://your-custom-domain.com",
    timeout=30,
    max_retries=3
)

# Validate with custom rules
result = client.validate_diagram(
    path="path/to/diagram.vsdx",
    rules=rules,
    callback_url="https://your-domain.com/webhook"
)

# Handle validation result
if result.passed:
    print("Validation passed!")
else:
    for error in result.errors:
        print(f"Error: {error.message}")
```

## Webhook Integration

### 1. Register Webhook

```python
# Register webhook endpoint
webhook = client.webhooks.register(
    url="https://your-domain.com/webhook",
    events=["validation.complete", "generation.complete"],
    secret="your-webhook-secret"
)
```

### 2. Implement Webhook Handler

```python
from flask import Flask, request
from lld_automation.webhooks import verify_signature

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    # Verify webhook signature
    signature = request.headers.get("X-Webhook-Signature")
    if not verify_signature(request.data, signature, "your-webhook-secret"):
        return "Invalid signature", 400

    # Process webhook payload
    event = request.json
    if event["type"] == "validation.complete":
        handle_validation_complete(event["data"])
    elif event["type"] == "generation.complete":
        handle_generation_complete(event["data"])

    return "OK", 200
```

### 3. Handle Webhook Events

```python
def handle_validation_complete(data):
    """Handle validation completion webhook."""
    diagram_id = data["diagram_id"]
    validation_results = data["validation_results"]
    
    if validation_results["passed"]:
        # Process successful validation
        update_diagram_status(diagram_id, "validated")
    else:
        # Handle validation failures
        notify_team(diagram_id, validation_results["errors"])

def handle_generation_complete(data):
    """Handle diagram generation completion webhook."""
    diagram_id = data["diagram_id"]
    diagram_path = data["diagram_path"]
    
    # Process generated diagram
    store_diagram(diagram_id, diagram_path)
```

## Error Handling

### Retry Logic

```python
from lld_automation import Client, RetryConfig
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure retry behavior
retry_config = RetryConfig(
    max_attempts=3,
    wait_min=1,
    wait_max=10,
    retry_on_status_codes=[500, 502, 503, 504]
)

client = Client(
    api_key="your-api-key",
    retry_config=retry_config
)

# Function with retry logic
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def validate_with_retry(diagram_path):
    try:
        return client.validate_diagram(diagram_path)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise
```

### Error Response Handling

```python
try:
    result = client.validate_diagram("path/to/diagram.vsdx")
except ValidationError as e:
    # Handle validation-specific errors
    logger.error(f"Validation error: {e.message}")
    for issue in e.issues:
        logger.error(f"- {issue.code}: {issue.message}")
except APIError as e:
    # Handle API-level errors
    logger.error(f"API error: {e.status_code} - {e.message}")
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
```

## Best Practices

### 1. Rate Limiting

```python
from lld_automation import Client, RateLimiter

# Configure rate limiter
rate_limiter = RateLimiter(
    max_requests=100,
    time_window=60  # 60 seconds
)

client = Client(
    api_key="your-api-key",
    rate_limiter=rate_limiter
)
```

### 2. Batch Processing

```python
# Process multiple diagrams efficiently
async def process_diagrams(diagram_paths):
    tasks = []
    for path in diagram_paths:
        task = client.validate_diagram_async(path)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### 3. Caching

```python
from lld_automation import Client, Cache

# Configure caching
cache = Cache(
    ttl=3600,  # 1 hour
    max_size=1000  # items
)

client = Client(
    api_key="your-api-key",
    cache=cache
)
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Environment Variables

```bash
# Required
export LLD_API_KEY=your-api-key
export LLD_API_URL=https://api.lldautomation.com

# Optional
export LLD_WEBHOOK_SECRET=your-webhook-secret
export LLD_LOG_LEVEL=INFO
export LLD_TIMEOUT=30
```

## Monitoring

### Health Checks

```python
# Monitor service health
health = client.health.check()
print(f"Service status: {health.status}")
print(f"API version: {health.version}")
```

### Metrics Collection

```python
# Collect usage metrics
metrics = client.metrics.get()
print(f"Total requests: {metrics.requests_total}")
print(f"Average response time: {metrics.avg_response_time}ms")
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('lld_automation')
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
```python
# Verify API key
try:
    client.auth.verify_key()
except AuthError as e:
    print(f"Auth error: {e.message}")
```

2. **Rate Limiting**
```python
# Check rate limit status
limits = client.rate_limits.get()
print(f"Remaining requests: {limits.remaining}")
print(f"Reset time: {limits.reset_at}")
```

3. **Webhook Delivery**
```python
# Check webhook delivery status
deliveries = client.webhooks.get_deliveries()
for delivery in deliveries:
    print(f"Status: {delivery.status}")
    print(f"Attempt count: {delivery.attempts}")
```

### Debugging Tools

```python
# Enable debug mode
client = Client(
    api_key="your-api-key",
    debug=True,
    log_level="DEBUG"
)

# Test connection
client.test_connection()
```

## Support

For integration support:
1. Check the [API Reference](api-reference.md)
2. Review [Validation Rules](validation-rules.md)
3. Contact support@lldautomation.com 