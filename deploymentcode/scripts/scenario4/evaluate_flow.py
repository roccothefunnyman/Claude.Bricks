"""
Evaluate different prompt strategies for the spec generator.
Compares outputs from different system prompts or deployment configs.
"""
import argparse
import json
import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


STRATEGIES = {
    "concise": (
        "You generate LEGO building specs as compact JSON. "
        "Be brief. Include only essential fields."
    ),
    "detailed": (
        "You are an expert LEGO building spec generator. Given a description, "
        "produce a comprehensive JSON specification including: height, style, "
        "facade, roof, windows, doors, colors, and special features."
    ),
    "creative": (
        "You are a creative LEGO architect. Generate unique, imaginative "
        "building specifications that push design boundaries while remaining "
        "buildable. Include unusual features and color combinations."
    ),
}

TEST_PROMPTS = [
    "3-story historic European townhouse with shop on ground floor",
    "Modern 2-story office building with glass facade",
    "Corner pub with bay windows and outdoor seating",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment", type=str, default="gpt-4o-mini",
                        help="OpenAI deployment name")
    args = parser.parse_args()

    endpoint = os.environ["OPENAI_ENDPOINT"]
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-08-01-preview",
    )

    results = {}
    for strategy_name, system_prompt in STRATEGIES.items():
        results[strategy_name] = []
        print(f"\n{'='*60}")
        print(f"Strategy: {strategy_name}")
        print(f"{'='*60}")

        for prompt in TEST_PROMPTS:
            response = client.chat.completions.create(
                model=args.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            output = response.choices[0].message.content
            results[strategy_name].append({
                "prompt": prompt,
                "output": output,
                "tokens": response.usage.total_tokens,
            })
            print(f"\nPrompt: {prompt}")
            print(f"Tokens: {response.usage.total_tokens}")
            print(f"Output: {output[:200]}...")

    # Save results
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to evaluation_results.json")


if __name__ == "__main__":
    main()
