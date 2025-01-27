from typing import Dict, Any
from models.visio_style_models import *
import functools

class StyleResolver:
    def __init__(self, style_guide):
        self.style_guide = style_guide
        self.cache = {}
        
    @functools.lru_cache(maxsize=128)
    def resolve_styles(self, element_type: str) -> Dict[str, Any]:
        """Enhanced resolution with 5-level cascading priorities"""
        if element_type in self.cache:
            return self.cache[element_type]
            
        styles = self._get_base_styles(element_type)
        styles = self._apply_domain_overrides(element_type, styles)
        styles = self._apply_template_overrides(styles)
        styles = self._apply_element_overrides(element_type, styles)
        self.cache[element_type] = styles
        return styles

    def _get_base_styles(self, element_type: str) -> Dict:
        base_map = {
            'schematic': {
                'inherits': ['shape', 'line', 'font'],
                'overrides': ['connector', 'annotation']
            },
            'floorplan': {
                'inherits': ['av_shape', 'av_line', 'font'],
                'overrides': ['dimension', 'symbol']
            }
        }
        # Multi-level inheritance resolution
        return self._resolve_inheritance_chain(base_map.get(element_type, {}))

    def _apply_domain_overrides(self, element_type: str, styles: Dict) -> Dict:
        # Implementation of _apply_domain_overrides method
        return styles

    def _apply_template_overrides(self, styles: Dict) -> Dict:
        # Implementation of _apply_template_overrides method
        return styles

    def _apply_element_overrides(self, element_type: str, styles: Dict) -> Dict:
        # Implementation of _apply_element_overrides method
        return styles

    def _finalize_styles(self, styles: Dict) -> Dict:
        # Implementation of _finalize_styles method
        return styles

    def _resolve_inheritance_chain(self, config: Dict) -> Dict:
        """Implement 3-level style inheritance with priority merging"""
        styles = {}
        
        if not config:
            return styles
        
        # Resolve base styles
        for base_type in config.get('inherits', []):
            base_style = self.style_guide.get_rule(base_type) or {}
            styles = self._merge_styles(styles, base_style)
        
        # Apply domain-specific overrides
        for override_type in config.get('overrides', []):
            override_style = self.style_guide.get_rule(override_type) or {}
            styles = self._merge_styles(styles, override_style, is_override=True)
        
        return styles

    def _merge_styles(self, base: Dict, new: Dict, is_override=False) -> Dict:
        """Deep merge style dictionaries with override handling"""
        merged = base.copy()
        for key, value in new.items():
            if isinstance(value, dict) and key in merged:
                merged[key] = self._merge_styles(merged[key], value, is_override)
            else:
                if is_override or key not in merged:
                    merged[key] = value
        return merged

    def convert_units(self, value: str) -> float:
        """Convert mm/pt units to Visio coordinates"""
        if 'mm' in value:
            return float(value.replace('mm', '')) * 0.03937 * 72  # mm to points
        if 'pt' in value:
            return float(value.replace('pt', ''))
        return float(value) 