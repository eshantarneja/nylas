from google.cloud import secretmanager
import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(secret_name: str):
    """
    Get a secret from environment variables or Google Cloud Secret Manager.
    Args:
        secret_name: Name of the secret to retrieve (e.g. 'OpenAPI_KEY')
    Returns:
        The secret value or raises an exception if not found.
    """
    try:
        # First try environment variables
        secret_value = os.getenv(secret_name)
        if secret_value:
            print(f"Successfully retrieved {secret_name} from environment")
            return secret_value

        # If environment variables fail, try Google Cloud Secret Manager
        project_id = "streamsales"
        
        try:
            client = secretmanager.SecretManagerServiceClient()
            print("Secret Manager client created")
            
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            if secret_value:
                return secret_value
        except Exception as e:
            print(f"Secret Manager error details: {str(e)}")
            print(f"Error type: {type(e).__name__}")

        raise ValueError(f"{secret_name} not found in environment variables or Secret Manager")

    except Exception as e:
        print(f"Failed to get {secret_name}: {str(e)}")
        raise ValueError(f"Could not retrieve {secret_name}: {str(e)}")