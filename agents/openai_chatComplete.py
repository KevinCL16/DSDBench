import logging
import pdb
import traceback

import openai
from agents.config.openai import API_KEY, BASE_URL, temperature
from agents.vllm_client import vllm_completion_with_backoff, check_vllm_server_health
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential, stop_after_delay, RetryError
)


def print_chat_message(messages):
    for message in messages:
        logging.info(f"{message['role']}: {message['content']}")


# @retry(wait=wait_random_exponential(min=0.1, max=20), stop=(stop_after_delay(30) | stop_after_attempt(100)))
def completion_with_backoff(messages, model_type, backend='OpenRouter'):
    """
    Unified completion function supporting multiple backends.
    
    Args:
        messages: List of message dictionaries
        model_type: Model type/name
        backend: Backend type ('OpenRouter', 'THU', 'vLLM')
    
    Returns:
        Response content string or None if failed
    """
    
    # Check if model_type indicates vLLM usage
    if model_type.startswith('vllm/') or backend == 'vLLM':
        return vllm_completion_with_backoff(messages, model_type)
    
    # Handle THU backend
    if backend == 'THU':
        try:
            from agents.config.openai import THU_API_KEY, THU_BASE_URL
            client = openai.OpenAI(
                api_key=THU_API_KEY,
                base_url=THU_BASE_URL,
            )
        except ImportError:
            logging.error("THU API configuration not found. Please check your config.")
            return None
    else:
        # Default OpenRouter backend
        client = openai.OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
        )

    try:
        response = client.chat.completions.create(
            model=model_type,
            messages=messages,
            temperature=temperature,
        )
        result = response.choices[0].message
        answer = result.content
        return answer
    except Exception as e:
        logging.error(f"API call failed: {e}")
        return None


def completion_with_log(messages, model_type, enable_log=False, backend='OpenRouter'):
    if enable_log:
        logging.info('========CHAT HISTORY========')
        print_chat_message(messages)
    response = completion_with_backoff(messages, model_type, backend)
    if enable_log:
        logging.info('========RESPONSE========')
        logging.info(response)
        logging.info('========RESPONSE END========')
    return response


def completion_for_4v(messages, model_type):
    openai.api_key = API_KEY
    openai.base_url = BASE_URL

    response = openai.chat.completions.create(
        model=model_type,
        messages=messages,
        temperature=temperature,
        # max_tokens=2000
    )

    result = response.choices[0].message
    answer = result.content
    return answer
