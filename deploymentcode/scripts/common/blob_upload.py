"""Utility: upload a local folder to a blob container."""
import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def upload_folder(storage_account: str, container_name: str, local_path: str, prefix: str = ""):
    """Upload all files in local_path to the specified blob container."""
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url, credential=DefaultAzureCredential())
    container_client = blob_service.get_container_client(container_name)

    uploaded = 0
    for root, _, files in os.walk(local_path):
        for fname in files:
            local_file = os.path.join(root, fname)
            rel_path = os.path.relpath(local_file, local_path).replace("\\", "/")
            blob_name = f"{prefix}/{rel_path}" if prefix else rel_path
            with open(local_file, "rb") as f:
                container_client.upload_blob(name=blob_name, data=f, overwrite=True)
            uploaded += 1

    print(f"Uploaded {uploaded} files to {container_name}/{prefix}")
    return uploaded
