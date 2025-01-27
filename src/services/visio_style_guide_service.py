import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from models.visio_style_models import *

logger = logging.getLogger(__name__)

class StyleGuideError(Exception):
    """Base exception for style guide errors"""

class VisioStyleGuideService:
    def __init__(self, rules_dir: str = "config/visio_style_rules"):
        self.rules = {}
        self.rules_dir = Path(rules_dir)
        self._load_rules()

    def _load_rules(self):
        """Load and validate all style rule files"""
        if not self.rules_dir.exists():
            raise StyleGuideError(f"Rules directory not found: {self.rules_dir}")

        for rule_file in self.rules_dir.glob("*.rules"):
            try:
                with open(rule_file, 'r') as f:
                    rule_data = json.load(f)
                rule_type = rule_file.stem.split('_')[0]
                self._validate_and_store(rule_type, rule_data)
            except Exception as e:
                logger.error(f"Error loading {rule_file}: {str(e)}")

    def _validate_and_store(self, rule_type: str, data: Dict[str, Any]):
        """Validate and store rule data using appropriate model"""
        validator_map = {
            'font': FontRules,
            'line': LineRules,
            'shape': ShapeRules,
            'page': PageRules
        }

        if rule_type not in validator_map:
            logger.warning(f"Unknown rule type: {rule_type}")
            return

        try:
            self.rules[rule_type] = validator_map[rule_type](**data)
        except Exception as e:
            logger.error(f"Validation failed for {rule_type} rules: {str(e)}")

    def get_style(self, element_type: str) -> Optional[BaseModel]:
        """Get style rules for a specific element type"""
        return self.rules.get(element_type)

    def reload_rules(self):
        """Reload all style rules from disk"""
        self.rules.clear()
        self._load_rules() 