from src.models.config_models import (
    APIConfig,
    StorageConfig,
    ProcessingConfig,
    VisioConfig,
    LoggingConfig,
    SystemConfig
)

default_api_config = APIConfig(
    openai_api_key="${OPENAI_API_KEY}",
    azure_form_recognizer_key="${AZURE_FORM_RECOGNIZER_KEY}",
    azure_storage_key="${AZURE_STORAGE_KEY}",
    endpoint_urls={
        "form_recognizer": "https://${AZURE_FORM_RECOGNIZER_ENDPOINT}",
        "openai": "https://api.openai.com/v1",
        "storage": "https://${AZURE_STORAGE_ACCOUNT}.blob.core.windows.net"
    }
)

default_storage_config = StorageConfig(
    storage_type="azure_blob",
    container_name="av-system-docs",
    connection_string="${AZURE_STORAGE_CONNECTION_STRING}",
    base_path="documents",
    retention_policy={
        "enabled": True,
        "days": 30
    }
)

default_processing_config = ProcessingConfig(
    max_file_size=10 * 1024 * 1024,  # 10MB
    supported_formats=[".pdf", ".docx", ".csv"],
    extraction_settings={
        "ocr_enabled": True,
        "language": "en",
        "confidence_threshold": 0.8
    },
    timeout_seconds=300,
    retry_attempts=3
)

default_visio_config = VisioConfig(
    stencil_path="stencils/av_components.vssx",
    default_page_size={"width": 1920, "height": 1080},
    shape_defaults={
        "font_size": 10,
        "font_family": "Arial",
        "fill_color": "#FFFFFF",
        "line_color": "#000000"
    },
    connector_defaults={
        "line_style": "Straight",
        "arrow_size": "Medium",
        "line_weight": 1
    },
    export_settings={
        "format": "pdf",
        "quality": "high",
        "include_metadata": True
    }
)

default_logging_config = LoggingConfig(
    log_level="INFO",
    log_file_path="logs/system.log",
    enable_console_logging=True,
    rotation_policy={
        "max_size_mb": 100,
        "backup_count": 5
    }
)

default_system_config = SystemConfig(
    api_config=default_api_config,
    storage_config=default_storage_config,
    processing_config=default_processing_config,
    visio_config=default_visio_config,
    logging_config=default_logging_config,
    environment="development"
) 