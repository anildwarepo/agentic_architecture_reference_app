import base64
import logging
import os
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
      
# Initialize Azure OpenAI client with Entra ID authentication
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(exclude_environment_credential=True,
                           exclude_cli_credential=True,
                           exclude_powershell_credential=True),
    "https://cognitiveservices.azure.com/.default"
)


token = token_provider()  # <- No await
print("Access Token:\n", token)


client = AzureOpenAI(
    azure_endpoint=endpoint,
    azure_ad_token_provider=token_provider,
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-02-01-preview"),
)


# IMAGE_PATH = "YOUR_IMAGE_PATH"
# encoded_image = base64.b64encode(open(IMAGE_PATH, 'rb').read()).decode('ascii')
chat_prompt = [
    {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": "You are an AI assistant that helps people find information."
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "hello"
            }
        ]
    },
    
]

# Include speech result if speech is enabled
messages = chat_prompt

completion = client.chat.completions.create(
    model=deployment,
    messages=messages,
    max_tokens=800,
    temperature=0.7,
    top_p=0.95,
    frequency_penalty=0,
    presence_penalty=0,
    stop=None,
    stream=False,
    store=True,
    metadata={"service_id": "test_service_id"},
)


print("Response:")
print(completion.choices[0].message.content)

