import os
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()

def get_secret(secret_name, default=None):
    try:
        if os.getenv("GAE_ENV", "").startswith("standard"):
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(name=name)
            return response.payload.data.decode("UTF-8")
        else:
            return os.getenv(secret_name, default)
    except Exception as e:
        print(f"Ошибка при загрузке секрета {secret_name}: {e}")
        return default