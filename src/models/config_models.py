from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class APIConfig:
    openai_api_key: str
    azure_form_recognizer_key: str
    azure_storage_key: str
    endpoint_urls: Dict[str, str]

@dataclass
class StorageConfig:
    storage_type: str  # 'azure_blob', 'file_system', etc.
    container_name: Optional[str]
    connection_string: Optional[str]
    base_path: Optional[str]
    retention_policy: Dict

@dataclass
class ProcessingConfig:
    max_file_size: int
    supported_formats: list
    extraction_settings: Dict
    timeout_seconds: int
    retry_attempts: int

@dataclass
class VisioConfig:
    stencil_path: str
    default_page_size: Dict[str, float]
    shape_defaults: Dict
    connector_defaults: Dict
    export_settings: Dict

@dataclass
class LoggingConfig:
    log_level: str
    log_file_path: str
    enable_console_logging: bool
    rotation_policy: Dict

@dataclass
class SystemConfig:
    api_config: APIConfig
    storage_config: StorageConfig
    processing_config: ProcessingConfig
    visio_config: VisioConfig
    logging_config: LoggingConfig
    environment: str  # 'development', 'production', etc. 