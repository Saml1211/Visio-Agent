from pydantic import BaseModel
from typing import Dict

class StyleAdoptionMetric(BaseModel):
    rule_type: str
    application_count: int = 0
    override_count: int = 0
    compliance_rate: float = 0.0

class QualityLearner:
    def __init__(self):
        self.metrics: Dict[str, StyleAdoptionMetric] = {}
        
    def track_application(self, rule_type: str, was_overridden: bool):
        if rule_type not in self.metrics:
            self.metrics[rule_type] = StyleAdoptionMetric(rule_type=rule_type)
            
        self.metrics[rule_type].application_count += 1
        if was_overridden:
            self.metrics[rule_type].override_count += 1
            
        self.metrics[rule_type].compliance_rate = (
            1 - (self.metrics[rule_type].override_count / 
                self.metrics[rule_type].application_count)
        )