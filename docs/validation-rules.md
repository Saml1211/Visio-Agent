# Validation Rules

## Overview

The LLD Automation Project implements a comprehensive set of validation rules to ensure diagrams meet industry standards and best practices. This document details all validation rules, their requirements, and how to configure them.

## Core Validation Categories

### 1. Color Accessibility

#### WCAG 2.1 Compliance
- **Contrast Ratio**: Minimum 4.5:1 for normal text, 3:1 for large text
- **Color Blindness**: Ensure diagrams are readable with common color vision deficiencies
- **Background Contrast**: Sufficient contrast between elements and background

#### Color Usage Rules
- **Maximum Colors**: No more than 7 distinct colors per diagram
- **Color Consistency**: Same color should represent same type of component/connection
- **Reserved Colors**:
  - Red: Reserved for errors/critical components
  - Yellow: Warnings/caution
  - Green: Status indicators/success

### 2. Text Readability

#### Font Requirements
- **Minimum Size**: 8pt for technical text, 10pt for labels
- **Font Family**: Sans-serif fonts (Arial, Calibri) for better readability
- **Text Contrast**: Must meet WCAG AA standards

#### Text Content
- **Abbreviations**: Must be consistent and documented
- **Case**: Title case for component names, sentence case for descriptions
- **Length**: Maximum 50 characters for labels, 200 for descriptions

### 3. Element Spacing

#### Component Spacing
- **Minimum Gap**: 20 pixels between components
- **Grouping**: Related components should be within 100 pixels
- **Grid Alignment**: Components should align to a 10-pixel grid

#### Layout Rules
- **Flow Direction**: Left-to-right or top-to-bottom
- **Hierarchy**: Clear visual hierarchy through spacing
- **Density**: Maximum 70% space utilization per page

### 4. Connection Validation

#### Connector Rules
- **Routing**: 90-degree angles preferred
- **Crossings**: Minimize connector crossings
- **Labels**: Must be readable and not overlap

#### Signal Flow
- **Direction**: Clear indication of signal flow
- **Types**: Different line styles for different connection types
- **Termination**: All connections must have valid start/end points

## Validation Levels

### 1. Basic Validation
```json
{
  "validation_rules": {
    "check_colors": true,
    "check_text": true,
    "check_spacing": true,
    "check_connections": true,
    "strict_mode": false
  }
}
```

- Performs essential checks
- Allows minor violations
- Suitable for draft diagrams

### 2. Strict Validation
```json
{
  "validation_rules": {
    "check_colors": true,
    "check_text": true,
    "check_spacing": true,
    "check_connections": true,
    "strict_mode": true
  }
}
```

- Enforces all rules strictly
- No violations allowed
- Required for final diagrams

## Custom Validation Rules

### 1. Creating Custom Rules

```python
from lld_automation.validation import BaseValidator

class CustomValidator(BaseValidator):
    def validate_custom_requirement(self, diagram):
        # Implementation
        pass
```

### 2. Rule Configuration

```yaml
# custom_rules.yaml
rules:
  custom_spacing:
    min_gap: 25
    max_gap: 100
  custom_colors:
    allowed_colors:
      - "#FF0000"
      - "#00FF00"
      - "#0000FF"
```

## Industry-Specific Rules

### 1. Network Diagrams
- Standardized network icons
- Clear subnet boundaries
- Proper protocol labeling

### 2. System Architecture
- Clear system boundaries
- Interface definitions
- Data flow indicators

### 3. Infrastructure Diagrams
- Capacity indicators
- Redundancy paths
- Environmental requirements

## Validation Process

### 1. Pre-validation
- File format check
- Template compliance
- Required metadata

### 2. Core Validation
- Color accessibility
- Text readability
- Element spacing
- Connection validity

### 3. Post-validation
- Overall complexity
- Documentation completeness
- Version compatibility

## Error Severity Levels

### 1. Critical Errors
- Must be fixed
- Blocks diagram approval
- Example: Invalid connections

### 2. Warnings
- Should be reviewed
- May be acceptable
- Example: Suboptimal spacing

### 3. Suggestions
- Optional improvements
- Best practice recommendations
- Example: Color scheme optimization

## Validation Response Format

```json
{
  "status": "completed",
  "timestamp": "2024-03-15T12:00:00Z",
  "results": {
    "passed": false,
    "score": 85,
    "errors": [
      {
        "severity": "critical",
        "code": "CONN_001",
        "message": "Invalid connection endpoint",
        "location": {
          "page": 1,
          "coordinates": {"x": 100, "y": 200}
        }
      }
    ],
    "warnings": [],
    "suggestions": []
  }
}
```

## Best Practices

### 1. Regular Validation
- Validate early and often
- Address critical errors immediately
- Track validation history

### 2. Rule Management
- Document custom rules
- Version control rule sets
- Regular rule reviews

### 3. Performance
- Batch validation requests
- Cache validation results
- Use incremental validation

## Troubleshooting

### Common Issues

1. **Color Contrast Failures**
   - Check background colors
   - Verify color codes
   - Consider color blindness modes

2. **Spacing Violations**
   - Use auto-arrange features
   - Check grid alignment
   - Verify component sizes

3. **Connection Errors**
   - Validate endpoints
   - Check connector styles
   - Verify signal flow

## Configuration Examples

### 1. Basic Configuration
```yaml
validation:
  color_checks:
    enabled: true
    wcag_level: "AA"
  text_checks:
    enabled: true
    min_size: 8
  spacing_checks:
    enabled: true
    min_gap: 20
```

### 2. Custom Rules
```yaml
custom_validation:
  rules:
    - name: "component_naming"
      pattern: "^[A-Z][a-z0-9_]+$"
      severity: "warning"
    - name: "max_connections"
      limit: 10
      severity: "error"
```

### 3. Environment-Specific
```yaml
development:
  strict_mode: false
  allow_warnings: true

production:
  strict_mode: true
  allow_warnings: false
``` 