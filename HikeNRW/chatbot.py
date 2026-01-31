from openai import OpenAI
import os


def get_message(messages, model="meta-llama-3.1-70b-instruct"):
    print(messages)
    # Start OpenAI client
    client = OpenAI(
        api_key=os.environ["GWDG_LLM_KEY"], base_url=os.environ["GWDG_LLM_URL"]
    )
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
    )
    return chat_completion.choices[0].message.content
