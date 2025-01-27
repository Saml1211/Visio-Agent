from src.services.ai_refinement_service import RefinementType, LLMCapability

# Define available LLMs and their capabilities
AVAILABLE_LLMS = [
    LLMCapability(
        name="gpt-4",
        supported_tasks=[RefinementType.DATA, RefinementType.VISIO],
        specializations=["technical_data", "layout_optimization", "av_systems"],
        max_input_size=8192,
        performance_metrics={
            "accuracy": 0.95,
            "speed": 0.85,
            "consistency": 0.90
        },
        cost_per_token=0.0002
    ),
    LLMCapability(
        name="gpt-3.5-turbo",
        supported_tasks=[RefinementType.DATA],
        specializations=["technical_data", "data_validation"],
        max_input_size=4096,
        performance_metrics={
            "accuracy": 0.85,
            "speed": 0.95,
            "consistency": 0.85
        },
        cost_per_token=0.0001
    ),
    LLMCapability(
        name="claude-2",
        supported_tasks=[RefinementType.VISIO],
        specializations=["layout_optimization", "visual_design"],
        max_input_size=100000,
        performance_metrics={
            "accuracy": 0.90,
            "speed": 0.80,
            "consistency": 0.95
        },
        cost_per_token=0.00015
    )
]

# Configuration for the refinement process
REFINEMENT_CONFIG = {
    "max_iterations": 3,
    "min_confidence": 0.95,
    "timeout_seconds": 300,
    "retry_attempts": 2,
    "parallel_processing": False,  # Enable for multiple LLMs in parallel
    
    # Data refinement specific settings
    "data_refinement": {
        "required_fields": [
            "manufacturer",
            "model",
            "specifications",
            "connections"
        ],
        "validation_rules": {
            "manufacturer": {"type": "string", "required": True},
            "model": {"type": "string", "required": True},
            "specifications": {"type": "dict", "required": True},
            "connections": {"type": "list", "required": True}
        },
        "confidence_thresholds": {
            "entity_extraction": 0.8,
            "relationship_mapping": 0.85,
            "data_validation": 0.9
        }
    },
    
    # Visio refinement specific settings
    "visio_refinement": {
        "layout_rules": {
            "min_component_distance": 50,
            "max_connector_length": 300,
            "alignment_threshold": 5
        },
        "style_rules": {
            "font_sizes": {"min": 8, "max": 14},
            "connector_styles": ["straight", "curved", "rightAngle"],
            "shape_spacing": {"horizontal": 100, "vertical": 75}
        },
        "confidence_thresholds": {
            "component_placement": 0.85,
            "connection_routing": 0.9,
            "overall_layout": 0.95
        }
    }
} 