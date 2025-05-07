"""
User feedback simulation for response quality evaluation.

This module provides utilities for simulating user feedback on agent responses.
"""
import random
import logging
import uuid
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from datetime import datetime

from tests.framework.quality.metrics import QualityDimension, QualityEvaluation

# Configure logging
logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Enum for feedback types."""
    RATING = "rating"
    THUMBS = "thumbs"
    COMMENT = "comment"
    CORRECTION = "correction"
    FOLLOW_UP = "follow_up"


class FeedbackSentiment(Enum):
    """Enum for feedback sentiment."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class UserFeedback:
    """
    Model for user feedback.
    """
    
    def __init__(
        self,
        id: str,
        type: FeedbackType,
        content: Dict[str, Any],
        sentiment: FeedbackSentiment,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize user feedback.
        
        Args:
            id: Feedback ID
            type: Feedback type
            content: Feedback content
            sentiment: Feedback sentiment
            timestamp: Optional timestamp
            metadata: Optional metadata
        """
        self.id = id
        self.type = type
        self.content = content
        self.sentiment = sentiment
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "sentiment": self.sentiment.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class FeedbackGenerator:
    """
    Generator for simulated user feedback.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize feedback generator.
        
        Args:
            seed: Optional random seed
        """
        if seed is not None:
            random.seed(seed)
    
    def generate_rating_feedback(
        self,
        query: str,
        response: str,
        evaluation: Optional[QualityEvaluation] = None,
        scale: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """
        Generate rating feedback.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Optional quality evaluation
            scale: Rating scale (default: 5)
            metadata: Optional metadata
            
        Returns:
            User feedback
        """
        # Determine rating based on evaluation if available
        if evaluation and evaluation.overall_score is not None:
            # Scale overall score to rating scale
            rating = round(evaluation.overall_score * scale / 10)
        else:
            # Generate random rating with bias towards higher ratings
            weights = [0.05, 0.1, 0.2, 0.3, 0.35][:scale]
            rating = random.choices(range(1, scale + 1), weights=weights)[0]
        
        # Determine sentiment based on rating
        if rating > scale * 0.7:
            sentiment = FeedbackSentiment.POSITIVE
        elif rating > scale * 0.4:
            sentiment = FeedbackSentiment.NEUTRAL
        else:
            sentiment = FeedbackSentiment.NEGATIVE
        
        # Create feedback
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            type=FeedbackType.RATING,
            content={
                "rating": rating,
                "scale": scale
            },
            sentiment=sentiment,
            metadata=metadata
        )
        
        return feedback
    
    def generate_thumbs_feedback(
        self,
        query: str,
        response: str,
        evaluation: Optional[QualityEvaluation] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """
        Generate thumbs feedback.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Optional quality evaluation
            metadata: Optional metadata
            
        Returns:
            User feedback
        """
        # Determine thumbs based on evaluation if available
        if evaluation and evaluation.overall_score is not None:
            # Convert overall score to thumbs
            thumbs_up = evaluation.overall_score >= 7.0
        else:
            # Generate random thumbs with bias towards thumbs up
            thumbs_up = random.random() < 0.7
        
        # Determine sentiment based on thumbs
        sentiment = FeedbackSentiment.POSITIVE if thumbs_up else FeedbackSentiment.NEGATIVE
        
        # Create feedback
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            type=FeedbackType.THUMBS,
            content={
                "thumbs_up": thumbs_up
            },
            sentiment=sentiment,
            metadata=metadata
        )
        
        return feedback
    
    def generate_comment_feedback(
        self,
        query: str,
        response: str,
        evaluation: Optional[QualityEvaluation] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """
        Generate comment feedback.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Optional quality evaluation
            metadata: Optional metadata
            
        Returns:
            User feedback
        """
        # Determine sentiment based on evaluation if available
        if evaluation and evaluation.overall_score is not None:
            if evaluation.overall_score >= 8.0:
                sentiment = FeedbackSentiment.POSITIVE
            elif evaluation.overall_score >= 5.0:
                sentiment = FeedbackSentiment.NEUTRAL
            else:
                sentiment = FeedbackSentiment.NEGATIVE
        else:
            # Generate random sentiment with bias towards positive
            weights = [0.6, 0.3, 0.1]
            sentiment = random.choices(
                [FeedbackSentiment.POSITIVE, FeedbackSentiment.NEUTRAL, FeedbackSentiment.NEGATIVE],
                weights=weights
            )[0]
        
        # Generate comment based on sentiment
        if sentiment == FeedbackSentiment.POSITIVE:
            comments = [
                "Great response, very helpful!",
                "Exactly what I needed, thanks!",
                "Very clear and informative.",
                "Perfect, this answers my question completely.",
                "Excellent explanation, I understand now."
            ]
        elif sentiment == FeedbackSentiment.NEUTRAL:
            comments = [
                "This is helpful, but could be more detailed.",
                "Thanks for the response, but I'm still a bit confused.",
                "Good information, but I was hoping for more specifics.",
                "This partially answers my question.",
                "Okay, but I need more clarification."
            ]
        else:
            comments = [
                "This doesn't answer my question.",
                "I'm still confused after reading this.",
                "This information seems incorrect.",
                "Not helpful at all.",
                "I need a more detailed explanation."
            ]
        
        comment = random.choice(comments)
        
        # Create feedback
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            type=FeedbackType.COMMENT,
            content={
                "comment": comment
            },
            sentiment=sentiment,
            metadata=metadata
        )
        
        return feedback
    
    def generate_correction_feedback(
        self,
        query: str,
        response: str,
        evaluation: Optional[QualityEvaluation] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """
        Generate correction feedback.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Optional quality evaluation
            metadata: Optional metadata
            
        Returns:
            User feedback
        """
        # Determine if correction is needed based on evaluation
        needs_correction = False
        correction_text = ""
        
        if evaluation:
            # Check accuracy score
            accuracy_score = evaluation.get_score(QualityDimension.ACCURACY)
            if accuracy_score and accuracy_score.score < 7.0:
                needs_correction = True
            
            # Check correctness score
            correctness_score = evaluation.get_score(QualityDimension.CORRECTNESS)
            if correctness_score and correctness_score.score < 7.0:
                needs_correction = True
        else:
            # Random chance of correction
            needs_correction = random.random() < 0.2
        
        # Generate correction text
        if needs_correction:
            corrections = [
                "Actually, the correct information is...",
                "I believe there's an error in your response. The correct answer is...",
                "This is not quite right. Let me clarify...",
                "There's a mistake in your response. It should be...",
                "I need to correct this information..."
            ]
            
            correction_text = random.choice(corrections)
        
        # Create feedback
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            type=FeedbackType.CORRECTION,
            content={
                "needs_correction": needs_correction,
                "correction": correction_text
            },
            sentiment=FeedbackSentiment.NEGATIVE if needs_correction else FeedbackSentiment.NEUTRAL,
            metadata=metadata
        )
        
        return feedback
    
    def generate_follow_up_feedback(
        self,
        query: str,
        response: str,
        evaluation: Optional[QualityEvaluation] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """
        Generate follow-up feedback.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Optional quality evaluation
            metadata: Optional metadata
            
        Returns:
            User feedback
        """
        # Determine if follow-up is needed based on evaluation
        needs_follow_up = False
        follow_up_text = ""
        
        if evaluation:
            # Check completeness score
            completeness_score = evaluation.get_score(QualityDimension.COMPLETENESS)
            if completeness_score and completeness_score.score < 8.0:
                needs_follow_up = True
        else:
            # Random chance of follow-up
            needs_follow_up = random.random() < 0.3
        
        # Generate follow-up text
        if needs_follow_up:
            follow_ups = [
                "Can you provide more details about...",
                "I'd like to know more about...",
                "Could you explain further...",
                "What about...",
                "How does this relate to..."
            ]
            
            follow_up_text = random.choice(follow_ups)
        
        # Create feedback
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            type=FeedbackType.FOLLOW_UP,
            content={
                "needs_follow_up": needs_follow_up,
                "follow_up": follow_up_text
            },
            sentiment=FeedbackSentiment.NEUTRAL,
            metadata=metadata
        )
        
        return feedback
    
    def generate_feedback(
        self,
        query: str,
        response: str,
        evaluation: Optional[QualityEvaluation] = None,
        feedback_types: Optional[List[FeedbackType]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[UserFeedback]:
        """
        Generate multiple types of feedback.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Optional quality evaluation
            feedback_types: Optional list of feedback types
            metadata: Optional metadata
            
        Returns:
            List of user feedback
        """
        # Use all feedback types if not specified
        if feedback_types is None:
            feedback_types = list(FeedbackType)
        
        # Generate feedback for each type
        feedback_list = []
        
        for feedback_type in feedback_types:
            if feedback_type == FeedbackType.RATING:
                feedback = self.generate_rating_feedback(query, response, evaluation, metadata=metadata)
            elif feedback_type == FeedbackType.THUMBS:
                feedback = self.generate_thumbs_feedback(query, response, evaluation, metadata=metadata)
            elif feedback_type == FeedbackType.COMMENT:
                feedback = self.generate_comment_feedback(query, response, evaluation, metadata=metadata)
            elif feedback_type == FeedbackType.CORRECTION:
                feedback = self.generate_correction_feedback(query, response, evaluation, metadata=metadata)
            elif feedback_type == FeedbackType.FOLLOW_UP:
                feedback = self.generate_follow_up_feedback(query, response, evaluation, metadata=metadata)
            else:
                continue
            
            feedback_list.append(feedback)
        
        return feedback_list


class FeedbackSimulator:
    """
    Simulator for user feedback.
    """
    
    def __init__(
        self,
        generator: Optional[FeedbackGenerator] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize feedback simulator.
        
        Args:
            generator: Optional feedback generator
            seed: Optional random seed
        """
        self.generator = generator or FeedbackGenerator(seed=seed)
        self.feedback_history = []
        
        if seed is not None:
            random.seed(seed)
    
    def simulate_feedback(
        self,
        query: str,
        response: str,
        evaluation: Optional[QualityEvaluation] = None,
        feedback_types: Optional[List[FeedbackType]] = None,
        feedback_probability: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[UserFeedback]:
        """
        Simulate user feedback.
        
        Args:
            query: User query
            response: Agent response
            evaluation: Optional quality evaluation
            feedback_types: Optional list of feedback types
            feedback_probability: Probability of providing feedback
            metadata: Optional metadata
            
        Returns:
            List of user feedback
        """
        # Determine if feedback is provided
        if random.random() > feedback_probability:
            return []
        
        # Generate feedback
        feedback_list = self.generator.generate_feedback(
            query=query,
            response=response,
            evaluation=evaluation,
            feedback_types=feedback_types,
            metadata=metadata
        )
        
        # Add to history
        self.feedback_history.extend(feedback_list)
        
        return feedback_list
    
    def get_feedback_history(
        self,
        feedback_type: Optional[FeedbackType] = None,
        sentiment: Optional[FeedbackSentiment] = None
    ) -> List[UserFeedback]:
        """
        Get feedback history.
        
        Args:
            feedback_type: Optional feedback type filter
            sentiment: Optional sentiment filter
            
        Returns:
            List of user feedback
        """
        result = []
        
        for feedback in self.feedback_history:
            if feedback_type and feedback.type != feedback_type:
                continue
            
            if sentiment and feedback.sentiment != sentiment:
                continue
            
            result.append(feedback)
        
        return result
    
    def get_feedback_statistics(
        self,
        feedback_type: Optional[FeedbackType] = None
    ) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Args:
            feedback_type: Optional feedback type filter
            
        Returns:
            Dictionary with feedback statistics
        """
        # Filter feedback
        feedback_list = self.get_feedback_history(feedback_type=feedback_type)
        
        if not feedback_list:
            return {
                "count": 0,
                "sentiment_distribution": {},
                "type_distribution": {}
            }
        
        # Count sentiments
        sentiment_counts = {
            FeedbackSentiment.POSITIVE.value: 0,
            FeedbackSentiment.NEUTRAL.value: 0,
            FeedbackSentiment.NEGATIVE.value: 0
        }
        
        for feedback in feedback_list:
            sentiment_counts[feedback.sentiment.value] += 1
        
        # Calculate sentiment distribution
        sentiment_distribution = {
            sentiment: count / len(feedback_list)
            for sentiment, count in sentiment_counts.items()
        }
        
        # Count types
        type_counts = {}
        
        for feedback in feedback_list:
            type_value = feedback.type.value
            if type_value not in type_counts:
                type_counts[type_value] = 0
            
            type_counts[type_value] += 1
        
        # Calculate type distribution
        type_distribution = {
            type_value: count / len(feedback_list)
            for type_value, count in type_counts.items()
        }
        
        # Calculate average rating
        ratings = []
        
        for feedback in feedback_list:
            if feedback.type == FeedbackType.RATING and "rating" in feedback.content:
                ratings.append(feedback.content["rating"])
        
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Calculate thumbs up ratio
        thumbs = []
        
        for feedback in feedback_list:
            if feedback.type == FeedbackType.THUMBS and "thumbs_up" in feedback.content:
                thumbs.append(1 if feedback.content["thumbs_up"] else 0)
        
        thumbs_up_ratio = sum(thumbs) / len(thumbs) if thumbs else None
        
        return {
            "count": len(feedback_list),
            "sentiment_distribution": sentiment_distribution,
            "type_distribution": type_distribution,
            "avg_rating": avg_rating,
            "thumbs_up_ratio": thumbs_up_ratio
        }
    
    def clear_history(self):
        """Clear feedback history."""
        self.feedback_history = []


# Example usage
if __name__ == "__main__":
    # Create simulator
    simulator = FeedbackSimulator(seed=42)
    
    # Simulate feedback
    feedback_list = simulator.simulate_feedback(
        query="What is the recommended tire pressure for a Boeing 737?",
        response="""
        The recommended tire pressure for a Boeing 737-800 is 200 psi for the main landing gear
        and 180 psi for the nose landing gear. These values may vary slightly based on the specific
        aircraft configuration and operating conditions.
        
        Always refer to the Aircraft Maintenance Manual (AMM) for the exact specifications for your
        aircraft. The tire pressure should be checked daily as part of the pre-flight inspection.
        """
    )
    
    # Print feedback
    for feedback in feedback_list:
        print(f"{feedback.type.value}: {feedback.sentiment.value}")
        print(f"Content: {feedback.content}")
        print()
    
    # Get statistics
    stats = simulator.get_feedback_statistics()
    print(f"Statistics: {stats}")
