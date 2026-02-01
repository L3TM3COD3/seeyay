"""
Google Cloud Secret Manager integration for Bot
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
    return response.payload.data.decode("UTF-8")


@lru_cache()
def get_bot_token() -> str:
    """Get Telegram bot token from Secret Manager or environment"""
    # First try environment variable (for local development)
    token = os.getenv("BOT_TOKEN")
    if token:
        return token.strip()
    
    # Then try Secret Manager
    return get_secret("telegram-bot-token").strip()


@lru_cache()
def get_gcp_config() -> dict:
    """Get GCP configuration"""
    project_id = os.getenv("GCP_PROJECT_ID")
    
    if not project_id:
        # Try to get from metadata server
        try:
            import requests
            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                headers={"Metadata-Flavor": "Google"},
                timeout=2
            )
            if response.status_code == 200:
                project_id = response.text
        except Exception:
            raise ValueError("Could not determine GCP project ID")
    
    return {
        "project_id": project_id,
        "location": os.getenv("GCP_LOCATION", "europe-west4")
    }
