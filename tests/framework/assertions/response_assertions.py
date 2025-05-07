"""
Assertion utilities for validating agent responses.

This module provides utilities for validating agent responses and checking
response quality and correctness.
"""
import re
from typing import Dict, List, Any, Optional, Union, Pattern
import json


class ResponseAssertions:
    """
    Assertion utilities for validating agent responses.
    """
    
    @staticmethod
    def assert_response_contains(response: str, expected_content: Union[str, List[str]]) -> bool:
        """
        Assert that the response contains the expected content.
        
        Args:
            response: Agent response
            expected_content: Expected content (string or list of strings)
            
        Returns:
            True if the assertion passes, False otherwise
        """
        if isinstance(expected_content, str):
            return expected_content in response
        else:
            return all(content in response for content in expected_content)
    
    @staticmethod
    def assert_response_matches_pattern(response: str, pattern: Union[str, Pattern]) -> bool:
        """
        Assert that the response matches the specified pattern.
        
        Args:
            response: Agent response
            pattern: Regular expression pattern
            
        Returns:
            True if the assertion passes, False otherwise
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.DOTALL)
        
        return bool(pattern.search(response))
    
    @staticmethod
    def assert_response_structure(response: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Assert that the response has the required structure.
        
        Args:
            response: Agent response as a dictionary
            required_keys: List of required keys
            
        Returns:
            True if the assertion passes, False otherwise
        """
        return all(key in response for key in required_keys)
    
    @staticmethod
    def assert_response_json_parsable(response: str) -> bool:
        """
        Assert that the response is valid JSON.
        
        Args:
            response: Agent response
            
        Returns:
            True if the assertion passes, False otherwise
        """
        try:
            json.loads(response)
            return True
        except json.JSONDecodeError:
            return False
    
    @staticmethod
    def assert_response_length(
        response: str, min_length: Optional[int] = None, max_length: Optional[int] = None
    ) -> bool:
        """
        Assert that the response length is within the specified range.
        
        Args:
            response: Agent response
            min_length: Minimum length (optional)
            max_length: Maximum length (optional)
            
        Returns:
            True if the assertion passes, False otherwise
        """
        response_length = len(response)
        
        if min_length is not None and response_length < min_length:
            return False
        
        if max_length is not None and response_length > max_length:
            return False
        
        return True
    
    @staticmethod
    def assert_response_relevance(
        response: str, query: str, threshold: float = 0.5
    ) -> bool:
        """
        Assert that the response is relevant to the query.
        
        This is a simple implementation that checks for keyword overlap.
        In a real implementation, this would use more sophisticated NLP techniques.
        
        Args:
            response: Agent response
            query: User query
            threshold: Relevance threshold (0.0 to 1.0)
            
        Returns:
            True if the assertion passes, False otherwise
        """
        # Simple implementation based on keyword overlap
        # In a real implementation, this would use more sophisticated NLP techniques
        
        # Normalize text
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Extract keywords (simple implementation)
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        if not query_words:
            return True  # Empty query
        
        # Count matching keywords
        matching_words = sum(1 for word in query_words if word in response_lower)
        
        # Calculate relevance score
        relevance_score = matching_words / len(query_words)
        
        return relevance_score >= threshold
    
    @staticmethod
    def assert_response_factual_accuracy(
        response: str, facts: Dict[str, Any], threshold: float = 0.8
    ) -> bool:
        """
        Assert that the response is factually accurate.
        
        This is a simple implementation that checks for fact presence.
        In a real implementation, this would use more sophisticated NLP techniques.
        
        Args:
            response: Agent response
            facts: Dictionary of facts to check
            threshold: Accuracy threshold (0.0 to 1.0)
            
        Returns:
            True if the assertion passes, False otherwise
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
            return True  # No facts to check
        
        accuracy_score = correct_facts / len(facts)
        
        return accuracy_score >= threshold
    
    @staticmethod
    def assert_response_completeness(
        response: str, required_elements: List[str], threshold: float = 0.7
    ) -> bool:
        """
        Assert that the response is complete.
        
        Args:
            response: Agent response
            required_elements: List of required elements
            threshold: Completeness threshold (0.0 to 1.0)
            
        Returns:
            True if the assertion passes, False otherwise
        """
        # Check each required element
        present_elements = 0
        for element in required_elements:
            if element.lower() in response.lower():
                present_elements += 1
        
        # Calculate completeness score
        if not required_elements:
            return True  # No required elements
        
        completeness_score = present_elements / len(required_elements)
        
        return completeness_score >= threshold
    
    @staticmethod
    def assert_response_format(response: str, expected_format: str) -> bool:
        """
        Assert that the response has the expected format.
        
        Args:
            response: Agent response
            expected_format: Expected format (e.g., 'markdown', 'json', 'html')
            
        Returns:
            True if the assertion passes, False otherwise
        """
        if expected_format.lower() == 'json':
            return ResponseAssertions.assert_response_json_parsable(response)
        elif expected_format.lower() == 'markdown':
            # Check for common markdown elements
            markdown_patterns = [
                r'#{1,6}\s+\w+',  # Headers
                r'\*\*\w+\*\*',    # Bold
                r'\*\w+\*',        # Italic
                r'```\w*\n[\s\S]*?\n```',  # Code blocks
                r'- \w+',          # List items
                r'\d+\. \w+',      # Numbered list items
                r'\[.+?\]\(.+?\)'  # Links
            ]
            return any(re.search(pattern, response) for pattern in markdown_patterns)
        elif expected_format.lower() == 'html':
            # Check for HTML tags
            return bool(re.search(r'<[a-z]+[^>]*>.*?</[a-z]+>', response, re.DOTALL))
        else:
            # Unknown format
            return True
    
    @staticmethod
    def assert_response_quality(
        response: str,
        query: str,
        expected_patterns: List[str],
        relevance_threshold: float = 0.5,
        completeness_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Comprehensive assessment of response quality.
        
        Args:
            response: Agent response
            query: User query
            expected_patterns: List of expected patterns
            relevance_threshold: Relevance threshold
            completeness_threshold: Completeness threshold
            
        Returns:
            Dictionary with quality assessment results
        """
        # Assess different quality dimensions
        relevance = ResponseAssertions.assert_response_relevance(
            response, query, relevance_threshold
        )
        
        completeness = ResponseAssertions.assert_response_completeness(
            response, expected_patterns, completeness_threshold
        )
        
        # Check for expected patterns
        pattern_matches = [
            pattern for pattern in expected_patterns
            if pattern.lower() in response.lower()
        ]
        
        # Calculate overall quality score
        quality_score = (
            (1.0 if relevance else 0.0) * 0.4 +  # 40% weight for relevance
            (len(pattern_matches) / len(expected_patterns) if expected_patterns else 1.0) * 0.3 +  # 30% weight for pattern matching
            (1.0 if completeness else 0.0) * 0.3  # 30% weight for completeness
        )
        
        return {
            "relevance": relevance,
            "completeness": completeness,
            "pattern_matches": pattern_matches,
            "missing_patterns": [p for p in expected_patterns if p not in pattern_matches],
            "quality_score": quality_score,
            "passes_threshold": quality_score >= 0.7  # 70% threshold for overall quality
        }


# Example usage
if __name__ == "__main__":
    # Sample response
    response = """
    The recommended tire pressure for a Boeing 737-800 is 200 psi for the main landing gear
    and 180 psi for the nose landing gear. These values may vary slightly based on the specific
    aircraft configuration and operating conditions.
    
    Always refer to the Aircraft Maintenance Manual (AMM) for the exact specifications for your
    aircraft. The tire pressure should be checked daily as part of the pre-flight inspection.
    """
    
    # Test assertions
    contains = ResponseAssertions.assert_response_contains(
        response, "recommended tire pressure"
    )
    print(f"Contains 'recommended tire pressure': {contains}")
    
    matches = ResponseAssertions.assert_response_matches_pattern(
        response, r"\d+ psi"
    )
    print(f"Matches pattern '\\d+ psi': {matches}")
    
    relevance = ResponseAssertions.assert_response_relevance(
        response, "What is the tire pressure for Boeing 737?"
    )
    print(f"Relevance: {relevance}")
    
    quality = ResponseAssertions.assert_response_quality(
        response,
        "What is the tire pressure for Boeing 737?",
        ["pressure values", "reference to manual", "inspection frequency"]
    )
    print(f"Quality assessment: {json.dumps(quality, indent=2)}")
