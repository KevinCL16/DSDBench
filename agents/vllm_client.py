import logging
import traceback
import requests
import json
from typing import List, Dict, Any, Optional
from agents.config.vllm import (
    VLLM_API_KEY, VLLM_BASE_URL, VLLM_TEMPERATURE,
    VLLM_MAX_TOKENS, VLLM_TOP_P, VLLM_FREQUENCY_PENALTY, VLLM_PRESENCE_PENALTY,
    VLLM_MODEL_CONFIGS
)


def print_chat_message(messages):
    """Print chat messages for debugging purposes."""
    for message in messages:
        logging.info(f"{message['role']}: {message['content']}")


class VLLMClient:
    """vLLM client wrapper that mimics OpenAI API format."""
    
    def __init__(self, 
                 api_key: str = VLLM_API_KEY,
                 base_url: str = VLLM_BASE_URL,
                 model_config: Optional[Dict[str, Any]] = None):
        """
        Initialize vLLM client.
        
        Args:
            api_key: API key (usually empty for local vLLM servers)
            base_url: Base URL of the vLLM server
            model_config: Model configuration dictionary
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model_config = model_config or {}
        
        # Set up session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        })
    
    def _prepare_request_data(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Prepare request data for vLLM API call."""
        # Get model-specific config if available
        model_name = model.replace('vllm/', '')  # Remove vllm/ prefix if present
        config = VLLM_MODEL_CONFIGS.get(model_name, {})
        
        # Merge configurations with priority: kwargs > model_config > default_config > VLLM_MODEL_CONFIGS
        request_data = {
            'model': config.get('model_name', model),
            'messages': messages,
            'temperature': kwargs.get('temperature', 
                                    self.model_config.get('temperature', 
                                                        config.get('temperature', VLLM_TEMPERATURE))),
            'max_tokens': kwargs.get('max_tokens',
                                   self.model_config.get('max_tokens',
                                                        config.get('max_tokens', VLLM_MAX_TOKENS))),
            'top_p': kwargs.get('top_p', 
                               self.model_config.get('top_p', VLLM_TOP_P)),
            'frequency_penalty': kwargs.get('frequency_penalty',
                                          self.model_config.get('frequency_penalty', VLLM_FREQUENCY_PENALTY)),
            'presence_penalty': kwargs.get('presence_penalty',
                                         self.model_config.get('presence_penalty', VLLM_PRESENCE_PENALTY)),
            'stream': kwargs.get('stream', False),
        }
        
        # Remove None values
        request_data = {k: v for k, v in request_data.items() if v is not None}
        
        return request_data
    
    def chat_completions_create(self, model: str, messages: List[Dict], **kwargs):
        """
        Create chat completion using vLLM server.
        
        Args:
            model: Model name
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Response object similar to OpenAI API
        """
        request_data = self._prepare_request_data(model, messages, **kwargs)
        
        try:
            # Make request to vLLM server
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                timeout=kwargs.get('timeout', 300)  # Default 5 minutes timeout
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Create a response object that mimics OpenAI's format
            class VLLMResponse:
                def __init__(self, data):
                    self.data = data
                    self.choices = [self.Choice(data['choices'][0])]
                
                class Choice:
                    def __init__(self, choice_data):
                        self.message = self.Message(choice_data['message'])
                        self.finish_reason = choice_data.get('finish_reason', 'stop')
                        self.index = choice_data.get('index', 0)
                    
                    class Message:
                        def __init__(self, message_data):
                            self.content = message_data['content']
                            self.role = message_data['role']
            
            return VLLMResponse(response_data)
            
        except requests.exceptions.RequestException as e:
            logging.error(f"vLLM API request failed: {e}")
            raise Exception(f"vLLM API request failed: {e}")
        except (KeyError, IndexError) as e:
            logging.error(f"vLLM API response parsing failed: {e}")
            raise Exception(f"vLLM API response parsing failed: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in vLLM client: {e}")
            logging.error(traceback.format_exc())
            raise


def vllm_completion_with_backoff(messages: List[Dict], 
                                model_type: str, 
                                max_retries: int = 3,
                                **kwargs):
    """
    vLLM completion function with retry logic.
    
    Args:
        messages: List of message dictionaries
        model_type: Model type (should start with 'vllm/' for vLLM models)
        max_retries: Maximum number of retry attempts
        **kwargs: Additional parameters for the API call
        
    Returns:
        Response content string or None if failed
    """
    # Ensure model_type starts with 'vllm/' for vLLM models
    if not model_type.startswith('vllm/'):
        model_type = f'vllm/{model_type}'
    
    client = VLLMClient()
    
    for attempt in range(max_retries):
        try:
            response = client.chat_completions_create(
                model=model_type,
                messages=messages,
                **kwargs
            )
            
            result = response.choices[0].message
            answer = result.content
            
            if answer:  # If answer is not empty, return it
                return answer
            
            # If answer is empty and not the last attempt, continue to next loop
            if attempt < max_retries - 1:
                logging.warning("Empty response received from vLLM. Retrying...")
                continue
                
        except Exception as e:
            logging.error(f"vLLM completion attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                continue
            else:
                return None
    
    # If all attempts failed, return None
    return None


def vllm_completion_with_log(messages: List[Dict], 
                           model_type: str, 
                           enable_log: bool = False,
                           **kwargs):
    """
    vLLM completion function with optional logging.
    
    Args:
        messages: List of message dictionaries
        model_type: Model type
        enable_log: Whether to enable logging
        **kwargs: Additional parameters
        
    Returns:
        Response content string
    """
    if enable_log:
        logging.info('========VLLM CHAT HISTORY========')
        print_chat_message(messages)
    
    response = vllm_completion_with_backoff(messages, model_type, **kwargs)
    
    if enable_log:
        logging.info('========VLLM RESPONSE========')
        logging.info(response)
        logging.info('========VLLM RESPONSE END========')
    
    return response


def check_vllm_server_health(base_url: str = VLLM_BASE_URL) -> bool:
    """
    Check if vLLM server is running and healthy.
    
    Args:
        base_url: Base URL of the vLLM server
        
    Returns:
        True if server is healthy, False otherwise
    """
    try:
        response = requests.get(f"{base_url.rstrip('/')}/health", timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def get_available_models(base_url: str = VLLM_BASE_URL) -> List[str]:
    """
    Get list of available models from vLLM server.
    
    Args:
        base_url: Base URL of the vLLM server
        
    Returns:
        List of available model names
    """
    try:
        response = requests.get(f"{base_url.rstrip('/')}/v1/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model['id'] for model in data.get('data', [])]
        return []
    except requests.exceptions.RequestException:
        return []


# Convenience functions for backward compatibility
def vllm_completion_for_4v(messages: List[Dict], model_type: str, **kwargs):
    """Compatibility function for 4v model completion."""
    return vllm_completion_with_backoff(messages, model_type, **kwargs)
