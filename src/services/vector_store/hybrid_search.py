from typing import List
from pydantic import BaseModel

class HybridResult(BaseModel):
    id: str
    content: str
    score: float

class HybridSearchMixin:
    def combine_results(
        self,
        keyword_results: List[HybridResult],
        vector_results: List[HybridResult],
        fusion_method: str = "reciprocal_rank"
    ) -> List[HybridResult]:
        """Combine keyword and vector search results using specified fusion method"""
        combined = {}
        
        # Reciprocal Rank Fusion (default)
        if fusion_method == "reciprocal_rank":
            for i, res in enumerate(keyword_results):
                combined[res.id] = combined.get(res.id, 0) + 1/(i+1)
            for i, res in enumerate(vector_results):
                combined[res.id] = combined.get(res.id, 0) + 1/(i+1)
                
        # Simple combination
        elif fusion_method == "simple":
            for res in keyword_results:
                combined[res.id] = combined.get(res.id, 0) + res.score
            for res in vector_results:
                combined[res.id] = combined.get(res.id, 0) + res.score
                
        # Convert to sorted list
        sorted_results = sorted(
            [HybridResult(id=k, content="", score=v) for k, v in combined.items()],
            key=lambda x: x.score,
            reverse=True
        )
        
        return sorted_results[:10] 