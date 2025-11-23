"""Protocol defining the interface for editorial operations (editing and refining content).

This protocol represents patterns applied for editing and refining content internally.
Agents implementing this protocol can validate, refine, and improve existing content.
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class EditorialProtocol(Protocol):
    """Protocol defining the interface for editorial operations.
    
    This protocol is for agents that perform editorial tasks such as:
    - Reviewing content and generating feedback
    - Validating content quality and correctness
    - Refining content based on review feedback
    - Improving content through iterative editing
    """
    
    async def review_content(
        self, content: Dict[str, Any], review_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Review content and generate detailed feedback.
        
        This generates a review that can be used as input to refine_content.
        
        Args:
            content: Content to review
            review_criteria: Criteria for review (e.g., {"focus": "clarity", "depth": "detailed"})
            
        Returns:
            Dict containing review feedback:
            {
                "overall_score": float,
                "feedback": str or List[str],
                "issues_found": List[Dict],
                "suggestions": List[Dict],
                "quality_metrics": Dict
            }
        """
        ...
    
    async def validate_content(self, content: Dict[str, Any]) -> bool:
        """Validate generated content.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        ...
    
    async def refine_content(
        self, content: Dict[str, Any], feedback: str | Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine content based on review feedback.
        
        Args:
            content: Content to refine
            feedback: Feedback from review_content() or string feedback
            
        Returns:
            Dict containing refined content
        """
        ...

