import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(key, default=None):
    return os.getenv(key, default)

# Database credentials
DB_USER = get_secret('DB_USER')
DB_PASSWORD = get_secret('DB_PASSWORD')
DB_HOST = get_secret('DB_HOST')
DB_PORT = get_secret('DB_PORT')

# Power BI
POWERBI_CLIENT_ID = get_secret('POWERBI_CLIENT_ID')
POWERBI_CLIENT_SECRET = get_secret('POWERBI_CLIENT_SECRET')
POWERBI_TENANT_ID = get_secret('POWERBI_TENANT_ID')

# Cloud storage
AWS_ACCESS_KEY = get_secret('AWS_ACCESS_KEY')
AWS_SECRET_KEY = get_secret('AWS_SECRET_KEY')
AZURE_CONNECTION_STRING = get_secret('AZURE_CONNECTION_STRING')
GCP_KEY_FILE = get_secret('GCP_KEY_FILE')

# API Keys
API_KEY = get_secret('API_KEY')

# Databricks
DATABRICKS_HOST = get_secret('DATABRICKS_HOST')
DATABRICKS_TOKEN = get_secret('DATABRICKS_TOKEN')
DATABRICKS_CLUSTER_ID = get_secret('DATABRICKS_CLUSTER_ID')
DATABRICKS_HTTP_PATH = get_secret('DATABRICKS_HTTP_PATH')