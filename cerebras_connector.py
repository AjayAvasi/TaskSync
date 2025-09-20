import os
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv('CEREBRAS_API_KEY')
if not api_key:
    raise ValueError("CEREBRAS_API_KEY environment variable is required")

client = Cerebras(
    api_key=api_key
)


def send_message(message: str, system_prompt: str, model: str = "qwen-3-coder-480b") -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": message
            }
        ],
        model=model,
        stream=False,
        max_completion_tokens=40000,
        temperature=0.7,
        top_p=0.8
    )

    return response.choices[0].message.content

