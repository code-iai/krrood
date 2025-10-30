"""Validators for EQL query code."""

from dataclasses import dataclass
from .models import ValidationResult


@dataclass
class EQLQueryValidator:
    """Validates generated EQL queries for syntax and executability."""
    
    def validate(self, query_code: str) -> ValidationResult:
        """
        Validate EQL query code.
        
        :param query_code: The generated EQL query code
        :return: Validation result with errors if any
        """
        try:
            # Attempt to compile the code
            compile(query_code, '<string>', 'exec')
            
            # Check for required EQL constructs
            if 'symbolic_mode' not in query_code:
                return ValidationResult(
                    is_valid=False,
                    error_message="Query must use symbolic_mode context"
                )
            
            if not any(quantifier in query_code for quantifier in ['an(', 'the(']):
                return ValidationResult(
                    is_valid=False,
                    error_message="Query must use a quantifier (an or the)"
                )
            
            return ValidationResult(is_valid=True)
            
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Syntax error: {str(e)}",
                syntax_errors=[str(e)]
            )
