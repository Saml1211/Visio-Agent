from typing import Dict, Type, Optional
from enum import Enum
import logging
from .base import VectorStoreProvider, VectorStoreError
from .pinecone_provider import PineconeProvider
from .chroma_provider import ChromaProvider
from .lilac_provider import LilacProvider

logger = logging.getLogger(__name__)

class VectorStoreType(str, Enum):
    """Supported vector store types"""
    PINECONE = "pinecone"
    CHROMA = "chroma"
    LILAC = "lilac"

class VectorStoreFactory:
    """Factory for creating vector store providers"""
    
    _providers: Dict[VectorStoreType, Type[VectorStoreProvider]] = {
        VectorStoreType.PINECONE: PineconeProvider,
        VectorStoreType.CHROMA: ChromaProvider,
        VectorStoreType.LILAC: LilacProvider
    }
    
    @classmethod
    def get_provider(
        cls,
        store_type: VectorStoreType
    ) -> VectorStoreProvider:
        """Get a vector store provider instance
        
        Args:
            store_type: Type of vector store to create
            
        Returns:
            VectorStoreProvider instance
            
        Raises:
            VectorStoreError: If provider type is not supported
        """
        try:
            if store_type not in cls._providers:
                raise VectorStoreError(f"Unsupported vector store type: {store_type}")
            
            provider_class = cls._providers[store_type]
            provider = provider_class()
            
            logger.info(f"Created vector store provider: {store_type}")
            return provider
            
        except Exception as e:
            logger.error(f"Error creating vector store provider: {str(e)}")
            raise VectorStoreError(f"Failed to create provider: {str(e)}")
    
    @classmethod
    def register_provider(
        cls,
        store_type: str,
        provider_class: Type[VectorStoreProvider]
    ) -> None:
        """Register a new vector store provider
        
        Args:
            store_type: Unique identifier for the provider type
            provider_class: Provider class implementing VectorStoreProvider
            
        Raises:
            VectorStoreError: If provider type already exists
        """
        try:
            if store_type in cls._providers:
                raise VectorStoreError(f"Provider type already exists: {store_type}")
            
            # Validate provider class
            if not issubclass(provider_class, VectorStoreProvider):
                raise VectorStoreError(
                    f"Provider class must implement VectorStoreProvider"
                )
            
            # Register provider
            cls._providers[VectorStoreType(store_type)] = provider_class
            logger.info(f"Registered new vector store provider: {store_type}")
            
        except Exception as e:
            logger.error(f"Error registering vector store provider: {str(e)}")
            raise VectorStoreError(f"Failed to register provider: {str(e)}")
    
    @classmethod
    def get_supported_types(cls) -> list[VectorStoreType]:
        """Get list of supported vector store types"""
        return list(cls._providers.keys())

    @staticmethod
    def create_provider(provider_type: str):
        providers = {
            "lilac": LilacProvider,
            "pinecone": PineconeProvider,
            "chroma": ChromaProvider
        }
        if provider_type not in providers:
            raise ValueError(f"Unsupported vector store: {provider_type}")
        return providers[provider_type]() 