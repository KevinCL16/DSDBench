"""
Exact Match Evaluator for DSDBench
Uses exact matching for code lines and error types, with LLM evaluation for error messages
"""
import json
import re
from typing import Dict, Any, List


class ExactMatchEvaluator:
    """Exact match evaluator that uses exact matching for code lines/error types and LLM for error messages"""
    
    def __init__(self):
        pass
    
    def evaluate_single_bug(self, llm_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate single bug detection using hybrid approach:
        - Exact match for cause_line, effect_line, error_type
        - LLM evaluation for error_message (to be done separately)
        
        Args:
            llm_output: LLM's detected error information
            ground_truth: Ground truth error information
            
        Returns:
            Dictionary with evaluation scores (excluding error_message_score)
        """
        return {
            'cause_line_score': self._exact_match(llm_output.get('cause_line', ''), ground_truth.get('cause_error_line', '')),
            'effect_line_score': self._exact_match(llm_output.get('effect_line', ''), ground_truth.get('effect_error_line', '')),
            'error_type_score': self._exact_match(llm_output.get('error_type', ''), ground_truth.get('error_type', ''))
        }
    
    def evaluate_multi_bug(self, llm_output_errors: List[Dict[str, Any]], ground_truth_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate multi-bug detection using hybrid approach
        
        Args:
            llm_output_errors: List of LLM detected errors
            ground_truth_errors: List of ground truth errors
            
        Returns:
            List of evaluation results for each LLM detected error
        """
        results = []
        
        for llm_error in llm_output_errors:
            best_match_score = 0
            best_match_result = None
            
            # Find the best matching ground truth error
            for gt_error in ground_truth_errors:
                match_result = self._calculate_hybrid_match(llm_error, gt_error)
                # Only consider exact match scores for finding best match
                exact_scores = [match_result['cause_line_score'], match_result['effect_line_score'], match_result['error_type_score']]
                total_exact_score = sum(exact_scores) / len(exact_scores)
                
                if total_exact_score > best_match_score:
                    best_match_score = total_exact_score
                    best_match_result = match_result
            
            if best_match_result is None:
                # No match found
                best_match_result = {
                    'cause_line_score': 0,
                    'effect_line_score': 0,
                    'error_type_score': 0
                }
            
            results.append(best_match_result)
        
        return results
    
    def _exact_match(self, output: str, ground_truth: str) -> int:
        """Check if two strings match exactly (case-insensitive)"""
        if not output or not ground_truth:
            return 0
        return 1 if output.strip().lower() == ground_truth.strip().lower() else 0
    
    def _calculate_hybrid_match(self, llm_error: Dict[str, Any], gt_error: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hybrid match between LLM error and ground truth error"""
        return {
            'cause_line_score': self._exact_match(llm_error.get('cause_line', ''), gt_error.get('cause_error_line', '')),
            'effect_line_score': self._exact_match(llm_error.get('effect_line', ''), gt_error.get('effect_error_line', '')),
            'error_type_score': self._exact_match(llm_error.get('error_type', ''), gt_error.get('error_type', ''))
        }


def create_exact_match_evaluator() -> ExactMatchEvaluator:
    """Factory function to create an exact match evaluator"""
    return ExactMatchEvaluator()
