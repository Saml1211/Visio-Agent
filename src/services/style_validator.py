from pydantic import ValidationError

class StyleValidator:
    VALID_UNITS = {'mm', 'pt', 'in', 'px'}
    
    def validate_rule(self, rule_data: Dict, rule_type: str) -> bool:
        """Perform 12-point validation check"""
        checks = [
            self._validate_unit_syntax,
            self._validate_color_values,
            self._validate_font_availability,
            self._validate_line_consistency,
            self._check_contrast_ratios,
            self._verify_template_compatibility,
            self._validate_visio_compatibility,
            self._check_symbol_availability,
            self._verify_measurement_units,
            self._validate_priority_levels,
            self._check_style_conflicts,
            self._verify_accessibility
        ]
        return all(check(rule_data, rule_type) for check in checks)

    def _validate_visio_compatibility(self, data: Dict, rule_type: str) -> bool:
        """Ensure styles map to valid Visio properties"""
        visio_properties = {
            'font': ['TextStyle', 'TextSize', 'TextColor'],
            'line': ['LineWeight', 'LineColor', 'LinePattern']
        }
        return all(prop in visio_properties.get(rule_type, []) for prop in data.keys()) 