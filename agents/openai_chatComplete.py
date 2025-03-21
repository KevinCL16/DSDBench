import logging
import pdb
import traceback

import openai
from agents.config.openai import API_KEY, BASE_URL, temperature, THU_BASE_URL, THU_API_KEY
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential, stop_after_delay, RetryError
)
from models.model_config import MODEL_CONFIG


def print_chat_message(messages):
    for message in messages:
        logging.info(f"{message['role']}: {message['content']}")


@retry(wait=wait_random_exponential(min=0.1, max=20), stop=(stop_after_delay(30) | stop_after_attempt(100)))
def completion_with_backoff(messages, model_type, backend='OpenRouter'):

    if model_type in MODEL_CONFIG.keys():

        port = MODEL_CONFIG[model_type]['port']
        model_full_path= MODEL_CONFIG[model_type]['model']
        
        openai_api_key = "EMPTY"
        openai_api_base = f"http://localhost:{port}/v1"

        client = openai.OpenAI(

            api_key=openai_api_key,
            base_url=openai_api_base,
        )
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(

                    model=model_full_path,
                    messages=messages,
                    temperature=temperature,
                    timeout=30*60,
                    max_tokens=4096,
                    
                )
                result = response.choices[0].message
                answer = result.content
                if answer:  # 如果answer不为空，直接返回
                    return answer
                # 如果answer为空且不是最后一次尝试，继续下一次循环
                if attempt < max_attempts - 1:
                    print("API CALL Empty response received. Retrying...")
                    continue
            except KeyError:

                return None
            except openai.BadRequestError as e:

                return e
        
        # 如果所有尝试都失败，返回None
        return None

    else:
        if backend == 'THU':
            client = openai.OpenAI(
                api_key=THU_API_KEY,
                base_url=THU_BASE_URL,
            )
        else:
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

        # except TypeError as e:
        #     print(e)
        #     return e

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return e


def completion_with_log(messages, model_type, enable_log=False):
    if enable_log:
        logging.info('========CHAT HISTORY========')
        print_chat_message(messages)
    response = completion_with_backoff(messages, model_type)
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
