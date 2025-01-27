from typing import List, Dict, DefaultDict

class ConsensusEngine:
    def __init__(self, config):
        self.quality_weights = config.get('model_weights')
        self.threshold_strategy = config.get('threshold_strategy')
        
    def analyze(self, results: List[dict]) -> dict:
        valid_results = [r for r in results if not r.get('error')]
        
        # Calculate dynamic threshold
        threshold = self._calculate_threshold(len(valid_results))
        
        # Weighted voting
        component_votes = defaultdict(float)
        for res in valid_results:
            model_weight = self.quality_weights.get(res['model'], 0.8)
            confidence = res['result'].get('confidence', 0.7)
            for component in res['result']['components']:
                component_votes[component['id']] += model_weight * confidence
                
        return {
            'components': [cid for cid, score in component_votes.items() if score >= threshold],
            'confidence_scores': component_votes
        } 