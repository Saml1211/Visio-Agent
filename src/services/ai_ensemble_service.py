from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json
import asyncio
import numpy as np
from pathlib import Path
from .exceptions import EnsembleError
from .ai_service_config import AIServiceConfig, AIProvider, TaskType

logger = logging.getLogger(__name__)

class EnsembleMethod(Enum):
    """Methods for combining model outputs"""
    MAJORITY_VOTE = "majority_vote"  # For discrete outputs
    WEIGHTED_AVERAGE = "weighted_average"  # For numeric outputs
    CONFIDENCE_BASED = "confidence_based"  # Select based on model confidence
    CROSS_VALIDATION = "cross_validation"  # Validate outputs against each other
    SEQUENTIAL = "sequential"  # Models refine output sequentially

@dataclass
class ModelWeight:
    """Configuration for model weighting"""
    model_name: str
    base_weight: float = 1.0
    confidence_multiplier: float = 1.0
    latency_penalty: float = 0.1
    error_penalty: float = 0.5
    success_rate: float = 1.0

@dataclass
class EnsembleResult:
    """Result from ensemble processing"""
    final_output: Any
    model_outputs: Dict[str, Any]
    weights_used: Dict[str, float]
    confidence_score: float
    processing_time_ms: float
    method_used: EnsembleMethod

class AIEnsembleService:
    """Service for managing AI model ensembles"""
    
    def __init__(
        self,
        config: AIServiceConfig,
        ensemble_config_path: Path,
        enable_logging: bool = True
    ):
        """Initialize the ensemble service
        
        Args:
            config: AI service configuration
            ensemble_config_path: Path to ensemble configuration file
            enable_logging: Whether to enable detailed logging
        """
        self.config = config
        self.ensemble_config_path = Path(ensemble_config_path)
        self.enable_logging = enable_logging
        
        # Load ensemble configurations
        self.ensembles: Dict[TaskType, List[ModelWeight]] = {}
        self.ensemble_methods: Dict[TaskType, EnsembleMethod] = {}
        self._load_ensemble_config()
        
        logger.info(
            f"Initialized AIEnsembleService with {len(self.ensembles)} "
            f"task ensembles"
        )
    
    def _load_ensemble_config(self) -> None:
        """Load ensemble configuration from file"""
        try:
            with open(self.ensemble_config_path) as f:
                config_data = json.load(f)
            
            # Load ensemble configurations for each task
            for task_str, task_config in config_data.items():
                task_type = TaskType(task_str)
                
                # Load model weights
                self.ensembles[task_type] = [
                    ModelWeight(**model_config)
                    for model_config in task_config["models"]
                ]
                
                # Load ensemble method
                self.ensemble_methods[task_type] = EnsembleMethod(
                    task_config["method"]
                )
                
        except Exception as e:
            logger.error(f"Error loading ensemble config: {str(e)}")
            raise EnsembleError(f"Failed to load ensemble config: {str(e)}")
    
    async def process_with_ensemble(
        self,
        task_type: TaskType,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> EnsembleResult:
        """Process input using model ensemble
        
        Args:
            task_type: Type of task to process
            input_data: Input data for processing
            context: Optional context for processing
            
        Returns:
            EnsembleResult containing final output and metadata
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            if task_type not in self.ensembles:
                raise EnsembleError(f"No ensemble configured for {task_type}")
            
            # Get model weights and method
            model_weights = self.ensembles[task_type]
            method = self.ensemble_methods[task_type]
            
            # Process with all models in parallel
            tasks = []
            for weight in model_weights:
                task = self._process_with_model(
                    weight.model_name,
                    input_data,
                    context
                )
                tasks.append(task)
            
            model_outputs = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Calculate current weights
            current_weights = self._calculate_weights(
                model_weights,
                model_outputs
            )
            
            # Combine outputs using selected method
            final_output, confidence = self._combine_outputs(
                model_outputs,
                current_weights,
                method
            )
            
            processing_time = (
                asyncio.get_event_loop().time() - start_time
            ) * 1000
            
            result = EnsembleResult(
                final_output=final_output,
                model_outputs=dict(zip(
                    [w.model_name for w in model_weights],
                    model_outputs
                )),
                weights_used=current_weights,
                confidence_score=confidence,
                processing_time_ms=processing_time,
                method_used=method
            )
            
            if self.enable_logging:
                self._log_ensemble_result(task_type, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ensemble processing: {str(e)}")
            raise EnsembleError(f"Ensemble processing failed: {str(e)}")
    
    async def _process_with_model(
        self,
        model_name: str,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Process input with a single model
        
        Args:
            model_name: Name of the model to use
            input_data: Input data for processing
            context: Optional context for processing
            
        Returns:
            Model output
        """
        try:
            # Get model-specific prompt
            prompt = await self.config.get_prompt(
                model_name,
                context
            )
            
            # Get AI provider for model
            provider = self.config.get_provider(model_name)
            
            # Process with model
            output = await provider.generate_text(
                prompt=prompt,
                input_data=input_data
            )
            
            return output
            
        except Exception as e:
            logger.error(f"Error processing with model {model_name}: {str(e)}")
            return None
    
    def _calculate_weights(
        self,
        model_weights: List[ModelWeight],
        model_outputs: List[Any]
    ) -> Dict[str, float]:
        """Calculate current weights for models
        
        Args:
            model_weights: Base model weights
            model_outputs: Outputs from each model
            
        Returns:
            Dict of model names to current weights
        """
        current_weights = {}
        
        for weight, output in zip(model_weights, model_outputs):
            # Start with base weight
            current_weight = weight.base_weight
            
            # Apply success rate
            current_weight *= weight.success_rate
            
            # Penalize for errors
            if output is None:
                current_weight *= (1 - weight.error_penalty)
            
            # Store calculated weight
            current_weights[weight.model_name] = max(0.0, current_weight)
        
        # Normalize weights
        total_weight = sum(current_weights.values())
        if total_weight > 0:
            current_weights = {
                k: v / total_weight
                for k, v in current_weights.items()
            }
        
        return current_weights
    
    def _combine_outputs(
        self,
        outputs: List[Any],
        weights: Dict[str, float],
        method: EnsembleMethod
    ) -> Tuple[Any, float]:
        """Combine outputs using specified method
        
        Args:
            outputs: List of model outputs
            weights: Dict of model weights
            method: Method for combining outputs
            
        Returns:
            Tuple of (combined output, confidence score)
        """
        try:
            if method == EnsembleMethod.MAJORITY_VOTE:
                return self._majority_vote(outputs, weights)
            elif method == EnsembleMethod.WEIGHTED_AVERAGE:
                return self._weighted_average(outputs, weights)
            elif method == EnsembleMethod.CONFIDENCE_BASED:
                return self._confidence_based(outputs, weights)
            elif method == EnsembleMethod.CROSS_VALIDATION:
                return self._cross_validation(outputs, weights)
            elif method == EnsembleMethod.SEQUENTIAL:
                return self._sequential_combine(outputs, weights)
            else:
                raise EnsembleError(f"Unsupported ensemble method: {method}")
                
        except Exception as e:
            logger.error(f"Error combining outputs: {str(e)}")
            raise EnsembleError(f"Output combination failed: {str(e)}")
    
    def _majority_vote(
        self,
        outputs: List[Any],
        weights: Dict[str, float]
    ) -> Tuple[Any, float]:
        """Combine outputs using weighted majority vote
        
        Args:
            outputs: List of model outputs
            weights: Dict of model weights
            
        Returns:
            Tuple of (selected output, confidence score)
        """
        # Count weighted votes for each unique output
        vote_counts = {}
        for output, weight in zip(outputs, weights.values()):
            if output is not None:
                output_str = str(output)  # Convert to string for comparison
                vote_counts[output_str] = (
                    vote_counts.get(output_str, 0) + weight
                )
        
        if not vote_counts:
            raise EnsembleError("No valid outputs for majority vote")
        
        # Find output with highest weighted votes
        max_votes = max(vote_counts.values())
        selected_output = None
        for output, votes in vote_counts.items():
            if votes == max_votes:
                selected_output = output
                break
        
        # Calculate confidence as ratio of winning votes to total
        confidence = max_votes / sum(vote_counts.values())
        
        return selected_output, confidence
    
    def _weighted_average(
        self,
        outputs: List[Any],
        weights: Dict[str, float]
    ) -> Tuple[Any, float]:
        """Combine numeric outputs using weighted average
        
        Args:
            outputs: List of numeric outputs
            weights: Dict of model weights
            
        Returns:
            Tuple of (averaged output, confidence score)
        """
        try:
            # Convert outputs to numeric values
            numeric_outputs = []
            valid_weights = []
            
            for output, weight in zip(outputs, weights.values()):
                if output is not None:
                    try:
                        value = float(output)
                        numeric_outputs.append(value)
                        valid_weights.append(weight)
                    except (ValueError, TypeError):
                        continue
            
            if not numeric_outputs:
                raise EnsembleError("No valid numeric outputs")
            
            # Calculate weighted average
            weighted_sum = sum(
                value * weight
                for value, weight in zip(numeric_outputs, valid_weights)
            )
            total_weight = sum(valid_weights)
            
            average = weighted_sum / total_weight if total_weight > 0 else 0
            
            # Calculate confidence based on output variance
            variances = [
                (value - average) ** 2
                for value in numeric_outputs
            ]
            confidence = 1.0 / (1.0 + np.mean(variances))
            
            return average, confidence
            
        except Exception as e:
            logger.error(f"Error in weighted average: {str(e)}")
            raise EnsembleError(f"Weighted average failed: {str(e)}")
    
    def _confidence_based(
        self,
        outputs: List[Any],
        weights: Dict[str, float]
    ) -> Tuple[Any, float]:
        """Select output based on model confidence
        
        Args:
            outputs: List of model outputs
            weights: Dict of model weights
            
        Returns:
            Tuple of (selected output, confidence score)
        """
        try:
            # Find output with highest weighted confidence
            max_confidence = -1
            selected_output = None
            
            for output, weight in zip(outputs, weights.values()):
                if output is not None:
                    # Calculate confidence score
                    confidence = weight * len(str(output))  # Simple heuristic
                    if confidence > max_confidence:
                        max_confidence = confidence
                        selected_output = output
            
            if selected_output is None:
                raise EnsembleError("No valid outputs for confidence selection")
            
            return selected_output, max_confidence
            
        except Exception as e:
            logger.error(f"Error in confidence-based selection: {str(e)}")
            raise EnsembleError(
                f"Confidence-based selection failed: {str(e)}"
            )
    
    def _cross_validation(
        self,
        outputs: List[Any],
        weights: Dict[str, float]
    ) -> Tuple[Any, float]:
        """Validate outputs against each other
        
        Args:
            outputs: List of model outputs
            weights: Dict of model weights
            
        Returns:
            Tuple of (selected output, confidence score)
        """
        try:
            # Calculate similarity scores between outputs
            similarity_scores = {}
            
            for i, output1 in enumerate(outputs):
                if output1 is None:
                    continue
                    
                score = 0
                for j, output2 in enumerate(outputs):
                    if i != j and output2 is not None:
                        # Calculate similarity (simple string comparison)
                        similarity = self._calculate_similarity(
                            str(output1),
                            str(output2)
                        )
                        score += similarity * list(weights.values())[j]
                
                similarity_scores[i] = score
            
            if not similarity_scores:
                raise EnsembleError("No valid outputs for cross validation")
            
            # Select output with highest similarity score
            best_index = max(
                similarity_scores.keys(),
                key=lambda k: similarity_scores[k]
            )
            confidence = similarity_scores[best_index]
            
            return outputs[best_index], confidence
            
        except Exception as e:
            logger.error(f"Error in cross validation: {str(e)}")
            raise EnsembleError(f"Cross validation failed: {str(e)}")
    
    def _sequential_combine(
        self,
        outputs: List[Any],
        weights: Dict[str, float]
    ) -> Tuple[Any, float]:
        """Combine outputs sequentially
        
        Args:
            outputs: List of model outputs
            weights: Dict of model weights
            
        Returns:
            Tuple of (final output, confidence score)
        """
        try:
            current_output = None
            confidence = 0.0
            
            # Process outputs in order of weight
            sorted_items = sorted(
                weights.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for model_name, weight in sorted_items:
                output = outputs[list(weights.keys()).index(model_name)]
                
                if output is not None:
                    if current_output is None:
                        current_output = output
                        confidence = weight
                    else:
                        # Merge outputs (simple string concatenation)
                        current_output = f"{current_output}\n{output}"
                        confidence = max(confidence, weight)
            
            if current_output is None:
                raise EnsembleError("No valid outputs for sequential combination")
            
            return current_output, confidence
            
        except Exception as e:
            logger.error(f"Error in sequential combination: {str(e)}")
            raise EnsembleError(f"Sequential combination failed: {str(e)}")
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple Levenshtein distance-based similarity
        try:
            from Levenshtein import ratio
            return ratio(str1, str2)
        except ImportError:
            # Fallback to simple comparison
            total_len = len(str1) + len(str2)
            if total_len == 0:
                return 1.0
            common_chars = sum(
                c1 == c2
                for c1, c2 in zip(str1, str2)
            )
            return 2 * common_chars / total_len
    
    def _log_ensemble_result(
        self,
        task_type: TaskType,
        result: EnsembleResult
    ) -> None:
        """Log ensemble processing result
        
        Args:
            task_type: Type of task processed
            result: Ensemble processing result
        """
        logger.info(
            f"Ensemble processing for {task_type.value}:\n"
            f"Method: {result.method_used.value}\n"
            f"Confidence: {result.confidence_score:.2f}\n"
            f"Processing time: {result.processing_time_ms:.2f}ms\n"
            f"Model weights: {result.weights_used}"
        )
        
        logger.debug(
            f"Model outputs for {task_type.value}:\n"
            f"{json.dumps(result.model_outputs, indent=2)}"
        )

# Limitations:
# 1. Simple string-based output comparison
# 2. Basic confidence scoring heuristics
# 3. Limited support for structured data comparison
# 4. No adaptive weight adjustment over time
# 5. No handling of model-specific output formats
# 6. Simple sequential combination strategy
# 7. No caching of intermediate results
# 8. Limited error recovery options 