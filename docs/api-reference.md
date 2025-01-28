# API Reference

## Overview

The LLD Automation Project provides a RESTful API for diagram validation and generation. This document details all available endpoints, their parameters, and response formats.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Diagram Validation

#### POST `/validate/diagram`

Validates a complete Visio diagram against defined rules and standards.

**Request Body:**
```json
{
  "diagram_path": "string",
  "validation_rules": {
    "check_colors": true,
    "check_text": true,
    "check_spacing": true,
    "check_connections": true
  },
  "strict_mode": false
}
```

**Response:**
```json
{
  "status": "success",
  "validation_results": {
    "passed": true,
    "score": 95.5,
    "issues": [
      {
        "type": "warning",
        "message": "Component spacing could be improved",
        "location": {
          "page": 1,
          "shape_id": "Shape123"
        }
      }
    ]
  }
}
```

#### POST `/validate/colors`

Validates color accessibility and contrast in the diagram.

**Request Body:**
```json
{
  "colors": [
    {
      "foreground": "#000000",
      "background": "#FFFFFF",
      "element_type": "text"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "contrast_ratio": 21.0,
      "wcag_aa_pass": true,
      "wcag_aaa_pass": true
    }
  ]
}
```

#### POST `/validate/text`

Validates text readability and formatting.

**Request Body:**
```json
{
  "text_elements": [
    {
      "content": "string",
      "font_size": 12,
      "font_family": "Arial"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "readability_score": 75.5,
      "is_readable": true,
      "suggestions": []
    }
  ]
}
```

#### POST `/validate/spacing`

Validates element spacing and layout.

**Request Body:**
```json
{
  "elements": [
    {
      "id": "string",
      "x": 0,
      "y": 0,
      "width": 100,
      "height": 50
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "spacing_score": 90.0,
    "crowded_areas": [],
    "suggestions": []
  }
}
```

### Diagram Generation

#### POST `/generate/diagram`

Generates a new Visio diagram based on provided specifications.

**Request Body:**
```json
{
  "template": "network_diagram",
  "components": [
    {
      "type": "router",
      "name": "Core Router",
      "connections": [
        {
          "to": "Switch1",
          "type": "ethernet"
        }
      ]
    }
  ],
  "layout_preferences": {
    "orientation": "horizontal",
    "spacing": "compact"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "diagram_path": "string",
  "generation_info": {
    "duration_ms": 1500,
    "components_placed": 10,
    "connections_routed": 15
  }
}
```

### System Status

#### GET `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
```

#### GET `/metrics`

Retrieve API usage metrics.

**Response:**
```json
{
  "requests_total": 1000,
  "validations_performed": 500,
  "diagrams_generated": 200,
  "average_response_time_ms": 250
}
```

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid color format provided",
    "details": {
      "field": "colors[0].foreground",
      "reason": "Must be a valid hex color code"
    }
  }
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input data
- `AUTH_ERROR`: Authentication failed
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Server error

## Rate Limiting

API endpoints are rate-limited to:
- 100 requests per minute per IP
- 1000 requests per hour per API key

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635789600
```

## Webhooks

The API supports webhooks for asynchronous operations:

1. Register webhook URL:
```json
POST /webhooks/register
{
  "url": "https://your-domain.com/webhook",
  "events": ["validation.complete", "generation.complete"]
}
```

2. Webhook payload format:
```json
{
  "event": "validation.complete",
  "timestamp": "2024-03-15T12:00:00Z",
  "data": {
    "diagram_id": "string",
    "validation_results": {}
  }
}
```

## SDK Examples

### Python

```python
from lld_automation import Client

client = Client(api_key="your-api-key")

# Validate diagram
result = client.validate_diagram("path/to/diagram.vsdx")
print(result.summary())

# Generate diagram
diagram = client.generate_diagram(
    template="network_diagram",
    components=[{"type": "router", "name": "Core Router"}]
)
print(diagram.path)
```

### TypeScript

```typescript
import { LLDClient } from 'lld-automation';

const client = new LLDClient({ apiKey: 'your-api-key' });

// Validate diagram
const result = await client.validateDiagram('path/to/diagram.vsdx');
console.log(result.summary());

// Generate diagram
const diagram = await client.generateDiagram({
  template: 'network_diagram',
  components: [{ type: 'router', name: 'Core Router' }]
});
console.log(diagram.path);
``` 