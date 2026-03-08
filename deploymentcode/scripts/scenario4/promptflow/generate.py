"""Generation node: call Azure OpenAI with retrieved context."""
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

SYSTEM_PROMPT = (
    "You are an expert LEGO building spec generator. Given a description of a "
    "building and reference specifications from similar buildings, produce a "
    "detailed JSON specification including: height (floors), style, facade type, "
    "roof type, window pattern, door placement, color palette, and special features. "
    "Output valid JSON only."
)


def generate(user_prompt: str, context: str, openai_endpoint: str,
             deployment_name: str = "gpt-4o-mini") -> str:
    """Generate a building spec using Azure OpenAI with RAG context."""
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )

    client = AzureOpenAI(
        azure_endpoint=openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-08-01-preview",
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Reference specifications:\n{context}\n\n"
            f"Generate a building spec for: {user_prompt}"
        )},
    ]

    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
    )

    return response.choices[0].message.content
