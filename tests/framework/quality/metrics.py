"""
Response quality metrics for evaluating agent responses.

This module provides metrics for evaluating response quality, including relevance,
accuracy, helpfulness, and other dimensions.
"""
import re
import logging
import statistics
from typing import Dict, List, Any, Optional, Union, Set
from enum import Enum
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Enum for quality dimensions."""
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    HELPFULNESS = "helpfulness"
    CLARITY = "clarity"
    CONCISENESS = "conciseness"
    COHERENCE = "coherence"
    CORRECTNESS = "correctness"
    SAFETY = "safety"


class QualityScore:
    """
    Model for quality scores.
    """
    
    def __init__(
        self,
        dimension: QualityDimension,
        score: float,
        max_score: float = 10.0,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a quality score.
        
        Args:
            dimension: Quality dimension
            score: Score value
            max_score: Maximum possible score
            timestamp: Optional timestamp
            metadata: Optional metadata
        """
        self.dimension = dimension
        self.score = score
        self.max_score = max_score
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "max_score": self.max_score,
            "normalized_score": self.score / self.max_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class QualityEvaluation:
    """
    Model for quality evaluations.
    """
    
    def __init__(
        self,
        query: str,
        response: str,
        scores: Optional[List[QualityScore]] = None,
        overall_score: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a quality evaluation.
        
        Args:
            query: User query
            response: Agent response
            scores: Optional list of quality scores
            overall_score: Optional overall score
            timestamp: Optional timestamp
            metadata: Optional metadata
        """
        self.query = query
        self.response = response
        self.scores = scores or []
        self.overall_score = overall_score
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def add_score(self, score: QualityScore):
        """
        Add a quality score.
        
        Args:
            score: Quality score
        """
        self.scores.append(score)
    
    def get_score(self, dimension: QualityDimension) -> Optional[QualityScore]:
        """
        Get score for the specified dimension.
        
        Args:
            dimension: Quality dimension
            
        Returns:
            Quality score or None if not found
        """
        for score in self.scores:
            if score.dimension == dimension:
                return score
        
        return None
    
    def calculate_overall_score(self, weights: Optional[Dict[QualityDimension, float]] = None):
        """
        Calculate overall score.
        
        Args:
            weights: Optional weights for each dimension
        """
        if not self.scores:
            self.overall_score = None
            return
        
        # Use equal weights if not specified
        if weights is None:
            weights = {score.dimension: 1.0 for score in self.scores}
        
        # Calculate weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        
        for score in self.scores:
            if score.dimension in weights:
                weight = weights[score.dimension]
                weighted_sum += (score.score / score.max_score) * weight
                total_weight += weight
        
        if total_weight > 0:
            self.overall_score = weighted_sum / total_weight
        else:
            self.overall_score = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "query": self.query,
            "response": self.response,
            "scores": [score.to_dict() for score in self.scores],
            "overall_score": self.overall_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class RelevanceMetric:
    """
    Metric for evaluating response relevance.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response relevance.
        
        This is a simple implementation that checks for keyword overlap.
        In a real implementation, this would use more sophisticated NLP techniques.
        
        Args:
            query: User query
            response: Agent response
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Simple implementation based on keyword overlap
        # In a real implementation, this would use more sophisticated NLP techniques
        
        # Normalize text
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Extract keywords (simple implementation)
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        if not query_words:
            return QualityScore(
                dimension=QualityDimension.RELEVANCE,
                score=max_score,
                max_score=max_score,
                metadata=metadata
            )
        
        # Count matching keywords
        matching_words = sum(1 for word in query_words if word in response_lower)
        
        # Calculate relevance score
        relevance_score = (matching_words / len(query_words)) * max_score
        
        return QualityScore(
            dimension=QualityDimension.RELEVANCE,
            score=relevance_score,
            max_score=max_score,
            metadata=metadata
        )


class AccuracyMetric:
    """
    Metric for evaluating response accuracy.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        facts: Dict[str, Any],
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response accuracy.
        
        This is a simple implementation that checks for fact presence.
        In a real implementation, this would use more sophisticated NLP techniques.
        
        Args:
            query: User query
            response: Agent response
            facts: Dictionary of facts to check
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Simple implementation based on fact presence
        # In a real implementation, this would use more sophisticated NLP techniques
        
        # Normalize text
        response_lower = response.lower()
        
        # Check each fact
        correct_facts = 0
        for fact_key, fact_value in facts.items():
            fact_str = str(fact_value).lower()
            if fact_str in response_lower:
                correct_facts += 1
        
        # Calculate accuracy score
        if not facts:
            accuracy_score = max_score
        else:
            accuracy_score = (correct_facts / len(facts)) * max_score
        
        return QualityScore(
            dimension=QualityDimension.ACCURACY,
            score=accuracy_score,
            max_score=max_score,
            metadata=metadata
        )


class CompletenessMetric:
    """
    Metric for evaluating response completeness.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        required_elements: List[str],
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response completeness.
        
        Args:
            query: User query
            response: Agent response
            required_elements: List of required elements
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Check each required element
        present_elements = 0
        for element in required_elements:
            if element.lower() in response.lower():
                present_elements += 1
        
        # Calculate completeness score
        if not required_elements:
            completeness_score = max_score
        else:
            completeness_score = (present_elements / len(required_elements)) * max_score
        
        return QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=completeness_score,
            max_score=max_score,
            metadata=metadata
        )


class HelpfulnessMetric:
    """
    Metric for evaluating response helpfulness.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        helpfulness_indicators: Optional[List[str]] = None,
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response helpfulness.
        
        Args:
            query: User query
            response: Agent response
            helpfulness_indicators: Optional list of helpfulness indicators
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Default helpfulness indicators
        if helpfulness_indicators is None:
            helpfulness_indicators = [
                "step", "procedure", "instruction",
                "guide", "how to", "example",
                "recommendation", "suggestion",
                "option", "alternative"
            ]
        
        # Check for helpfulness indicators
        indicator_count = 0
        for indicator in helpfulness_indicators:
            if indicator.lower() in response.lower():
                indicator_count += 1
        
        # Calculate helpfulness score
        if not helpfulness_indicators:
            helpfulness_score = max_score
        else:
            # Use diminishing returns formula
            helpfulness_score = min(max_score, (indicator_count / len(helpfulness_indicators)) * max_score * 2)
        
        return QualityScore(
            dimension=QualityDimension.HELPFULNESS,
            score=helpfulness_score,
            max_score=max_score,
            metadata=metadata
        )


class ClarityMetric:
    """
    Metric for evaluating response clarity.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response clarity.
        
        This is a simple implementation based on sentence length and structure.
        In a real implementation, this would use more sophisticated NLP techniques.
        
        Args:
            query: User query
            response: Agent response
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return QualityScore(
                dimension=QualityDimension.CLARITY,
                score=0,
                max_score=max_score,
                metadata=metadata
            )
        
        # Calculate sentence lengths
        sentence_lengths = [len(s.split()) for s in sentences]
        
        # Calculate statistics
        avg_length = statistics.mean(sentence_lengths)
        
        # Penalize very short or very long sentences
        length_penalty = 0
        if avg_length < 5:
            length_penalty = (5 - avg_length) / 5
        elif avg_length > 25:
            length_penalty = (avg_length - 25) / 25
        
        # Check for structure indicators
        structure_indicators = [
            "first", "second", "third", "finally",
            "next", "then", "additionally", "moreover",
            "in conclusion", "to summarize"
        ]
        
        structure_score = 0
        for indicator in structure_indicators:
            if indicator.lower() in response.lower():
                structure_score += 1
        
        structure_score = min(1.0, structure_score / 3)
        
        # Calculate clarity score
        clarity_score = max_score * (1 - length_penalty) * (0.7 + 0.3 * structure_score)
        
        return QualityScore(
            dimension=QualityDimension.CLARITY,
            score=clarity_score,
            max_score=max_score,
            metadata=metadata
        )


class ConcisenesMetric:
    """
    Metric for evaluating response conciseness.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response conciseness.
        
        Args:
            query: User query
            response: Agent response
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Count words
        response_words = len(response.split())
        query_words = len(query.split())
        
        # Calculate ratio
        ratio = response_words / max(1, query_words)
        
        # Penalize very verbose responses
        if ratio < 2:
            conciseness_score = max_score
        elif ratio < 5:
            conciseness_score = max_score * (1 - (ratio - 2) / 3)
        else:
            conciseness_score = max_score * 0.2
        
        return QualityScore(
            dimension=QualityDimension.CONCISENESS,
            score=conciseness_score,
            max_score=max_score,
            metadata=metadata
        )


class CoherenceMetric:
    """
    Metric for evaluating response coherence.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response coherence.
        
        This is a simple implementation based on transition words and structure.
        In a real implementation, this would use more sophisticated NLP techniques.
        
        Args:
            query: User query
            response: Agent response
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Check for transition words
        transition_words = [
            "however", "therefore", "thus", "consequently",
            "furthermore", "moreover", "in addition", "besides",
            "accordingly", "as a result", "for example", "for instance",
            "in contrast", "on the other hand", "similarly", "likewise"
        ]
        
        transition_count = 0
        for word in transition_words:
            if word.lower() in response.lower():
                transition_count += 1
        
        # Calculate transition score
        transition_score = min(1.0, transition_count / 3)
        
        # Check for paragraph structure
        paragraphs = response.split("\n\n")
        paragraph_score = min(1.0, len(paragraphs) / 3)
        
        # Calculate coherence score
        coherence_score = max_score * (0.5 + 0.3 * transition_score + 0.2 * paragraph_score)
        
        return QualityScore(
            dimension=QualityDimension.COHERENCE,
            score=coherence_score,
            max_score=max_score,
            metadata=metadata
        )


class CorrectnessMetric:
    """
    Metric for evaluating response correctness.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        reference_response: str,
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response correctness against a reference response.
        
        This is a simple implementation based on word overlap.
        In a real implementation, this would use more sophisticated NLP techniques.
        
        Args:
            query: User query
            response: Agent response
            reference_response: Reference response
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Normalize text
        response_lower = response.lower()
        reference_lower = reference_response.lower()
        
        # Extract words
        response_words = set(re.findall(r'\b\w+\b', response_lower))
        reference_words = set(re.findall(r'\b\w+\b', reference_lower))
        
        if not reference_words:
            return QualityScore(
                dimension=QualityDimension.CORRECTNESS,
                score=0,
                max_score=max_score,
                metadata=metadata
            )
        
        # Calculate overlap
        overlap = len(response_words.intersection(reference_words))
        
        # Calculate correctness score
        correctness_score = (overlap / len(reference_words)) * max_score
        
        return QualityScore(
            dimension=QualityDimension.CORRECTNESS,
            score=correctness_score,
            max_score=max_score,
            metadata=metadata
        )


class SafetyMetric:
    """
    Metric for evaluating response safety.
    """
    
    @staticmethod
    def evaluate(
        query: str,
        response: str,
        unsafe_patterns: Optional[List[str]] = None,
        max_score: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response safety.
        
        Args:
            query: User query
            response: Agent response
            unsafe_patterns: Optional list of unsafe patterns
            max_score: Maximum possible score
            metadata: Optional metadata
            
        Returns:
            Quality score
        """
        # Default unsafe patterns
        if unsafe_patterns is None:
            unsafe_patterns = [
                "password", "credential", "secret", "token",
                "social security", "credit card", "account number",
                "confidential", "private", "sensitive"
            ]
        
        # Check for unsafe patterns
        unsafe_count = 0
        for pattern in unsafe_patterns:
            if pattern.lower() in response.lower():
                unsafe_count += 1
        
        # Calculate safety score
        if not unsafe_patterns:
            safety_score = max_score
        else:
            safety_score = max_score * (1 - unsafe_count / len(unsafe_patterns))
        
        return QualityScore(
            dimension=QualityDimension.SAFETY,
            score=safety_score,
            max_score=max_score,
            metadata=metadata
        )


class QualityEvaluator:
    """
    Evaluator for response quality.
    """
    
    def __init__(self):
        """Initialize the quality evaluator."""
        self.evaluations = []
    
    def evaluate(
        self,
        query: str,
        response: str,
        reference_data: Optional[Dict[str, Any]] = None,
        dimensions: Optional[List[QualityDimension]] = None,
        weights: Optional[Dict[QualityDimension, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityEvaluation:
        """
        Evaluate response quality.
        
        Args:
            query: User query
            response: Agent response
            reference_data: Optional reference data
            dimensions: Optional list of dimensions to evaluate
            weights: Optional weights for each dimension
            metadata: Optional metadata
            
        Returns:
            Quality evaluation
        """
        # Use all dimensions if not specified
        if dimensions is None:
            dimensions = list(QualityDimension)
        
        # Create evaluation
        evaluation = QualityEvaluation(
            query=query,
            response=response,
            metadata=metadata
        )
        
        # Evaluate each dimension
        for dimension in dimensions:
            if dimension == QualityDimension.RELEVANCE:
                score = RelevanceMetric.evaluate(query, response)
            elif dimension == QualityDimension.ACCURACY:
                if reference_data and "facts" in reference_data:
                    score = AccuracyMetric.evaluate(query, response, reference_data["facts"])
                else:
                    continue
            elif dimension == QualityDimension.COMPLETENESS:
                if reference_data and "required_elements" in reference_data:
                    score = CompletenessMetric.evaluate(query, response, reference_data["required_elements"])
                else:
                    continue
            elif dimension == QualityDimension.HELPFULNESS:
                if reference_data and "helpfulness_indicators" in reference_data:
                    score = HelpfulnessMetric.evaluate(query, response, reference_data["helpfulness_indicators"])
                else:
                    score = HelpfulnessMetric.evaluate(query, response)
            elif dimension == QualityDimension.CLARITY:
                score = ClarityMetric.evaluate(query, response)
            elif dimension == QualityDimension.CONCISENESS:
                score = ConcisenesMetric.evaluate(query, response)
            elif dimension == QualityDimension.COHERENCE:
                score = CoherenceMetric.evaluate(query, response)
            elif dimension == QualityDimension.CORRECTNESS:
                if reference_data and "reference_response" in reference_data:
                    score = CorrectnessMetric.evaluate(query, response, reference_data["reference_response"])
                else:
                    continue
            elif dimension == QualityDimension.SAFETY:
                if reference_data and "unsafe_patterns" in reference_data:
                    score = SafetyMetric.evaluate(query, response, reference_data["unsafe_patterns"])
                else:
                    score = SafetyMetric.evaluate(query, response)
            else:
                continue
            
            # Add score to evaluation
            evaluation.add_score(score)
        
        # Calculate overall score
        evaluation.calculate_overall_score(weights)
        
        # Add evaluation to list
        self.evaluations.append(evaluation)
        
        return evaluation
    
    def get_evaluations(
        self,
        dimension: Optional[QualityDimension] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[QualityEvaluation]:
        """
        Get evaluations matching the specified criteria.
        
        Args:
            dimension: Optional dimension filter
            min_score: Optional minimum score filter
            max_score: Optional maximum score filter
            
        Returns:
            List of matching evaluations
        """
        result = []
        
        for evaluation in self.evaluations:
            if dimension:
                score = evaluation.get_score(dimension)
                if not score:
                    continue
                
                if min_score is not None and score.score < min_score:
                    continue
                
                if max_score is not None and score.score > max_score:
                    continue
            elif min_score is not None or max_score is not None:
                if evaluation.overall_score is None:
                    continue
                
                if min_score is not None and evaluation.overall_score < min_score:
                    continue
                
                if max_score is not None and evaluation.overall_score > max_score:
                    continue
            
            result.append(evaluation)
        
        return result
    
    def get_average_score(self, dimension: QualityDimension) -> Optional[float]:
        """
        Get average score for the specified dimension.
        
        Args:
            dimension: Quality dimension
            
        Returns:
            Average score or None if no scores
        """
        scores = []
        
        for evaluation in self.evaluations:
            score = evaluation.get_score(dimension)
            if score:
                scores.append(score.score)
        
        if not scores:
            return None
        
        return statistics.mean(scores)
    
    def get_score_distribution(self, dimension: QualityDimension) -> Dict[str, float]:
        """
        Get score distribution for the specified dimension.
        
        Args:
            dimension: Quality dimension
            
        Returns:
            Dictionary with score distribution statistics
        """
        scores = []
        
        for evaluation in self.evaluations:
            score = evaluation.get_score(dimension)
            if score:
                scores.append(score.score)
        
        if not scores:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "stdev": None
            }
        
        result = {
            "count": len(scores),
            "min": min(scores),
            "max": max(scores),
            "mean": statistics.mean(scores),
            "median": statistics.median(scores)
        }
        
        if len(scores) > 1:
            result["stdev"] = statistics.stdev(scores)
        else:
            result["stdev"] = 0
        
        return result
    
    def clear(self):
        """Clear all evaluations."""
        self.evaluations = []


# Example usage
if __name__ == "__main__":
    # Create evaluator
    evaluator = QualityEvaluator()
    
    # Evaluate response
    evaluation = evaluator.evaluate(
        query="What is the recommended tire pressure for a Boeing 737?",
        response="""
        The recommended tire pressure for a Boeing 737-800 is 200 psi for the main landing gear
        and 180 psi for the nose landing gear. These values may vary slightly based on the specific
        aircraft configuration and operating conditions.
        
        Always refer to the Aircraft Maintenance Manual (AMM) for the exact specifications for your
        aircraft. The tire pressure should be checked daily as part of the pre-flight inspection.
        """,
        reference_data={
            "facts": {
                "main_gear_pressure": "200 psi",
                "nose_gear_pressure": "180 psi"
            },
            "required_elements": [
                "tire pressure",
                "main landing gear",
                "nose landing gear",
                "maintenance manual"
            ]
        }
    )
    
    # Print evaluation
    print(f"Overall score: {evaluation.overall_score:.2f}")
    
    for score in evaluation.scores:
        print(f"{score.dimension.value}: {score.score:.2f}/{score.max_score:.2f}")
