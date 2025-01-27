from typing import List, Optional, Dict, Any
import asyncio
from tqdm import tqdm
from src.models.rag_models import VectorDocument
from src.services.vector_store.base_provider import VectorStoreProvider
from src.models.rag_models import DocumentSchema

class BatchProcessor:
    def __init__(
        self,
        vector_store: VectorStoreProvider,
        schema: DocumentSchema,
        batch_size: int = 100,
        max_retries: int = 3
    ):
        self.vector_store = vector_store
        self.schema = schema
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._current_batch = []
        self._results = []
        self._errors = []

    async def process_batch(self, documents: List[VectorDocument]) -> Dict[str, Any]:
        """Process a batch of documents with validation and error handling"""
        valid_docs = []
        for doc in documents:
            if errors := self.schema.validate(doc):
                self._errors.extend(errors)
            else:
                valid_docs.append(doc)

        for attempt in range(self.max_retries):
            try:
                ids = await self.vector_store.add_documents(valid_docs)
                return {
                    "success": len(ids),
                    "failed": len(valid_docs) - len(ids),
                    "errors": self._errors
                }
            except Exception as e:
                if attempt == self.max_retries - 1:
                    self._errors.append(f"Final failure: {str(e)}")
                    return {
                        "success": 0,
                        "failed": len(valid_docs),
                        "errors": self._errors
                    }
                await asyncio.sleep(2 ** attempt)

        return {"success": 0, "failed": 0, "errors": []}

    async def stream_processing(
        self,
        document_stream,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Process documents from a stream with progress tracking"""
        total_docs = 0
        with tqdm(desc="Processing documents") as pbar:
            while True:
                batch = []
                try:
                    for _ in range(self.batch_size):
                        doc = await document_stream.__anext__()
                        batch.append(doc)
                        total_docs += 1
                except StopAsyncIteration:
                    pass

                if not batch:
                    break

                result = await self.process_batch(batch)
                self._results.append(result)
                
                if progress_callback:
                    progress_callback({
                        "processed": sum(r['success'] for r in self._results),
                        "remaining": total_docs - sum(r['success'] + r['failed'] for r in self._results)
                    })
                
                pbar.update(len(batch))
                pbar.set_postfix({
                    "success": sum(r['success'] for r in self._results),
                    "errors": len(self._errors)
                })

        return {
            "total_processed": sum(r['success'] for r in self._results),
            "total_failed": sum(r['failed'] for r in self._results),
            "total_errors": len(self._errors),
            "batches": self._results
        } 