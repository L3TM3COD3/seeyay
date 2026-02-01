"""
Google Cloud Secret Manager integration
"""
from google.cloud import secretmanager
from functools import lru_cache
import os


_client = None


def get_secret_client():
    """Get Secret Manager client (singleton)"""
    global _client
    if _client is None:
        _client = secretmanager.SecretManagerServiceClient()
    return _client


def get_secret(secret_id: str, project_id: str = None) -> str:
    """
    Get secret value from Secret Manager
    
    Args:
        secret_id: The ID of the secret (e.g., "bot-token")
        project_id: GCP project ID (defaults to environment variable)
        
    Returns:
        The secret value as a string
    """
    if project_id is None:
        project_id = os.getenv("GCP_PROJECT_ID")
    
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is not set")
    
    client = get_secret_client()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8").strip()


@lru_cache()
def get_bot_token() -> str:
    """Get Telegram bot token from Secret Manager"""
    # First try environment variable (for local development or Cloud Run secrets)
    token = os.getenv("BOT_TOKEN")
    if token:
        return token.strip()
    
    # Then try Secret Manager
    return get_secret("telegram-bot-token")


@lru_cache()
def get_gcp_project_id() -> str:
    """Get GCP project ID"""
    # From environment variable
    project_id = os.getenv("GCP_PROJECT_ID")
    if project_id:
        return project_id
    
    # From metadata server (when running in GCP)
    try:
        import requests
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/project/project-id",
            headers={"Metadata-Flavor": "Google"},
            timeout=2
        )
        if response.status_code == 200:
            return response.text
    except Exception:
        pass
    
    raise ValueError("Could not determine GCP project ID")
