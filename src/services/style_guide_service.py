def get_routing_config(self, diagram_type: str) -> RoutingConfig:
    return RoutingConfig(**self.style_rules["routing"][diagram_type]) 