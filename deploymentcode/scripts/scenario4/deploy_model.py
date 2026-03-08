"""
Deploy the fine-tuned model to an Azure OpenAI endpoint.

After the fine-tuning job succeeds, retrieve the model ID and deploy it.
"""
import argparse
import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=str, required=True,
                        help="Fine-tuning job ID from fine_tune_job.py")
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

    # Get the fine-tuned model ID
    ft_job = client.fine_tuning.jobs.retrieve(args.job_id)
    if ft_job.status != "succeeded":
        print(f"Job status is '{ft_job.status}', not 'succeeded'. Wait for completion.")
        return

    model_id = ft_job.fine_tuned_model
    print(f"Fine-tuned model: {model_id}")
    print()
    print("Deploy via Azure CLI:")
    print(f"  az cognitiveservices account deployment create \\")
    print(f"    --name $(jq -r '.openai_endpoint.value' scripts/tf_outputs.json | sed 's|https://||;s|.openai.azure.com/||') \\")
    print(f"    --resource-group $RESOURCE_GROUP \\")
    print(f"    --deployment-name ft-spec-generator \\")
    print(f"    --model-name {model_id} \\")
    print(f"    --model-version 1 \\")
    print(f"    --model-format OpenAI \\")
    print(f"    --sku-capacity 10 \\")
    print(f"    --sku-name Standard")


if __name__ == "__main__":
    main()
