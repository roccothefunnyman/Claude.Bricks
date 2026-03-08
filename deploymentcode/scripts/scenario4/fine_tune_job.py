"""
Submit a fine-tuning job to Azure OpenAI.

References:
  https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/fine-tuning

IMPORTANT: Fine-tuning availability is region- and model-specific.
Supported regions (as of 2025): East US, East US 2, North Central US,
Sweden Central, Switzerland West.
"""
import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


def main():
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

    # 1. Upload training file
    training_path = "../../data/scenario4/training_data.jsonl"
    with open(training_path, "rb") as f:
        training_file = client.files.create(file=f, purpose="fine-tune")
    print(f"Uploaded training file: {training_file.id}")

    # 2. Submit fine-tuning job
    ft_job = client.fine_tuning.jobs.create(
        training_file=training_file.id,
        model="gpt-4o-mini",
    )
    print(f"Fine-tuning job submitted: {ft_job.id}")
    print(f"Status: {ft_job.status}")
    print()
    print("Monitor with:")
    print(f'  status = client.fine_tuning.jobs.retrieve("{ft_job.id}")')
    print("  print(status.status)  # running, succeeded, failed")
    print()
    print("Cost warning: Fine-tuned model hosting costs ~$1.70/hour.")
    print("Delete the deployment when not actively using it.")


if __name__ == "__main__":
    main()
