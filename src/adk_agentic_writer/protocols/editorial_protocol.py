"""Protocol defining the interface for editorial operations (editing and refining content).

This protocol represents patterns applied for editing and refining content internally.
Agents implementing this protocol can validate, refine, and improve existing content.
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class EditorialProtocol(Protocol):
    """Protocol defining the interface for editorial operations.
    
    This protocol is for agents that perform editorial tasks such as:
    - Validating content quality and correctness
    - Refining content based on feedback
    - Improving content through iterative editing
    """
    
    async def generate_content(self, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content based on prompt and parameters.
        
        Args:
            prompt: Content generation prompt
            parameters: Generation parameters
            
        Returns:
            Dict containing generated content
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
    
    async def refine_content(self, content: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """Refine content based on feedback.
        
        Args:
            content: Content to refine
            feedback: Feedback for refinement
            
        Returns:
            Dict containing refined content
        """
        ...

