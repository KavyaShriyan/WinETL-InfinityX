# Data source configuration for multiple database types
import sys
import io
import os
import json
import requests
import pandas as pd

# Import database drivers conditionally to avoid import errors
try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import pymysql
except ImportError:
    pymysql = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import oracledb
except ImportError:
    oracledb = None

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

try:
    from cassandra.cluster import Cluster
except (ImportError, Exception) as e:
    Cluster = None
    # Suppress Cassandra driver initialization errors on Python 3.12+
    pass

try:
    import boto3
except ImportError:
    boto3 = None

try:
    from azure.storage.blob import BlobServiceClient
except ImportError:
    BlobServiceClient = None

try:
    from google.cloud import storage
except ImportError:
    storage = None

try:
    from databricks import sql
except ImportError:
    sql = None

# Set stdout encoding to handle unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class DataSourceConnector:
    def __init__(self, config):
        self.config = config
        self.connection = None

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def execute_query(self, query):
        raise NotImplementedError

    def get_data(self, query):
        raise NotImplementedError

class SQLServerConnector(DataSourceConnector):
    def connect(self):
        if pyodbc is None:
            raise Exception("pyodbc driver not installed. Please install pyodbc.")
        try:
            conn_str = (
                f"DRIVER={self.config.get('driver', 'ODBC Driver 17 for SQL Server')};"
                f"SERVER={self.config['server']};"
                f"DATABASE={self.config['database']};"
                f"Trusted_Connection={self.config.get('trusted_connection', 'yes')};"
            )
            # Only add username/password if using SQL Server authentication
            if self.config.get('trusted_connection', 'yes').lower() != 'yes':
                if 'username' in self.config and 'password' in self.config:
                    conn_str += f"UID={self.config['username']};PWD={self.config['password']};"
            
            self.connection = pyodbc.connect(conn_str)
            print("[SUCCESS] SQL Server connection established.")
            return self.connection
        except Exception as e:
            print(f"[ERROR] SQL Server connection failed: {str(e)}")
            raise e

    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def get_data(self, query):
        cursor = self.execute_query(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

class AzureSynapseConnector(DataSourceConnector):
    def connect(self):
        if pyodbc is None:
            raise Exception("pyodbc driver not installed. Please install pyodbc.")
        try:
            # Azure Synapse connection string
            conn_str = (
                f"DRIVER={self.config.get('driver', 'ODBC Driver 17 for SQL Server')};"
                f"SERVER={self.config['server']};"
                f"DATABASE={self.config['database']};"
            )
            
            # Azure Synapse supports both SQL Auth and Azure AD Auth
            if 'username' in self.config and 'password' in self.config:
                conn_str += f"UID={self.config['username']};PWD={self.config['password']};"
            elif self.config.get('authentication') == 'ActiveDirectoryInteractive':
                conn_str += "Authentication=ActiveDirectoryInteractive;"
            elif self.config.get('authentication') == 'ActiveDirectoryPassword':
                conn_str += f"Authentication=ActiveDirectoryPassword;UID={self.config['username']};PWD={self.config['password']};"
            
            # Additional Synapse-specific options
            if self.config.get('encrypt'):
                conn_str += "Encrypt=yes;"
            if self.config.get('trust_server_certificate'):
                conn_str += "TrustServerCertificate=yes;"
            
            self.connection = pyodbc.connect(conn_str)
            print("[SUCCESS] Azure Synapse connection established.")
            return self.connection
        except Exception as e:
            print(f"[ERROR] Azure Synapse connection failed: {str(e)}")
            raise e

    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def get_data(self, query):
        cursor = self.execute_query(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

class MicrosoftFabricConnector(DataSourceConnector):
    def connect(self):
        if pyodbc is None:
            raise Exception("pyodbc driver not installed. Please install pyodbc.")
        try:
            # Microsoft Fabric SQL endpoint connection
            conn_str = (
                f"DRIVER={self.config.get('driver', 'ODBC Driver 17 for SQL Server')};"
                f"SERVER={self.config['server']};"
                f"DATABASE={self.config['database']};"
            )
            
            # Fabric supports SQL Auth and Azure AD Auth
            if 'username' in self.config and 'password' in self.config:
                conn_str += f"UID={self.config['username']};PWD={self.config['password']};"
            elif self.config.get('authentication') == 'ActiveDirectoryInteractive':
                conn_str += "Authentication=ActiveDirectoryInteractive;"
            elif self.config.get('authentication') == 'ActiveDirectoryPassword':
                conn_str += f"Authentication=ActiveDirectoryPassword;UID={self.config['username']};PWD={self.config['password']};"
            elif self.config.get('authentication') == 'ActiveDirectoryServicePrincipal':
                conn_str += f"Authentication=ActiveDirectoryServicePrincipal;UID={self.config['client_id']};PWD={self.config['client_secret']};"
            
            # Fabric requires encryption
            conn_str += "Encrypt=yes;"
            if self.config.get('trust_server_certificate', True):
                conn_str += "TrustServerCertificate=yes;"
            
            self.connection = pyodbc.connect(conn_str)
            print("[SUCCESS] Microsoft Fabric connection established.")
            return self.connection
        except Exception as e:
            print(f"[ERROR] Microsoft Fabric connection failed: {str(e)}")
            raise e

    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def get_data(self, query):
        cursor = self.execute_query(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

class MySQLConnector(DataSourceConnector):
    def connect(self):
        if pymysql is None:
            print("[ERROR] pymysql not installed")
            return None
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
            print("[SUCCESS] MySQL connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] MySQL connection failed:", str(e))
            return None

    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def get_data(self, query):
        cursor = self.execute_query(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

class PostgreSQLConnector(DataSourceConnector):
    def connect(self):
        if psycopg2 is None:
            print("[ERROR] psycopg2 not installed")
            return None
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
            print("[SUCCESS] PostgreSQL connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] PostgreSQL connection failed:", str(e))
            return None

    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def get_data(self, query):
        cursor = self.execute_query(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

class OracleConnector(DataSourceConnector):
    def connect(self):
        if oracledb is None:
            raise Exception("oracledb driver not installed. Please install oracledb.")
        try:
            dsn = oracledb.makedsn(self.config['host'], self.config['port'], service_name=self.config['service_name'])
            self.connection = oracledb.connect(
                user=self.config['username'],
                password=self.config['password'],
                dsn=dsn
            )
            print("[SUCCESS] Oracle connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] Oracle connection failed:", str(e))
            return None

    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def get_data(self, query):
        cursor = self.execute_query(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

class MongoDBConnector(DataSourceConnector):
    def connect(self):
        try:
            self.connection = MongoClient(self.config['uri'])
            print("[SUCCESS] MongoDB connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] MongoDB connection failed:", str(e))
            return None

    def get_data(self, collection_name, query=None):
        db = self.connection[self.config['database']]
        collection = db[collection_name]
        if query:
            data = list(collection.find(query))
        else:
            data = list(collection.find())
        # Convert to DataFrame-like structure
        if data:
            columns = list(data[0].keys())
            rows = [list(doc.values()) for doc in data]
            return columns, rows
        return [], []

class CassandraConnector(DataSourceConnector):
    def connect(self):
        try:
            cluster = Cluster(self.config['contact_points'])
            self.connection = cluster.connect(self.config['keyspace'])
            print("[SUCCESS] Cassandra connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] Cassandra connection failed:", str(e))
            return None

    def get_data(self, query):
        rows = self.connection.execute(query)
        if rows:
            columns = list(rows[0]._fields)
            data = [list(row) for row in rows]
            return columns, data
        return [], []

class DynamoDBConnector(DataSourceConnector):
    def connect(self):
        try:
            self.connection = boto3.resource('dynamodb', region_name=self.config['region'])
            print("[SUCCESS] DynamoDB connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] DynamoDB connection failed:", str(e))
            return None

    def get_data(self, table_name):
        table = self.connection.Table(table_name)
        response = table.scan()
        items = response['Items']
        if items:
            columns = list(items[0].keys())
            rows = [list(item.values()) for item in items]
            return columns, rows
        return [], []

class FileConnector(DataSourceConnector):
    def get_data(self, file_path):
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        elif file_path.endswith('.xml'):
            df = pd.read_xml(file_path)
        else:
            raise ValueError("Unsupported file format")
        columns = list(df.columns)
        rows = df.values.tolist()
        return columns, rows

class S3Connector(DataSourceConnector):
    def connect(self):
        try:
            self.connection = boto3.client('s3',
                aws_access_key_id=self.config['access_key'],
                aws_secret_access_key=self.config['secret_key']
            )
            print("[SUCCESS] S3 connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] S3 connection failed:", str(e))
            return None

    def get_data(self, bucket, key):
        obj = self.connection.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read().decode('utf-8')
        # Assume CSV for simplicity
        from io import StringIO
        df = pd.read_csv(StringIO(body))
        columns = list(df.columns)
        rows = df.values.tolist()
        return columns, rows

class AzureBlobConnector(DataSourceConnector):
    def connect(self):
        try:
            self.connection = BlobServiceClient.from_connection_string(self.config['connection_string'])
            print("[SUCCESS] Azure Blob connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] Azure Blob connection failed:", str(e))
            return None

    def get_data(self, container, blob):
        blob_client = self.connection.get_blob_client(container=container, blob=blob)
        data = blob_client.download_blob().readall().decode('utf-8')
        from io import StringIO
        df = pd.read_csv(StringIO(data))
        columns = list(df.columns)
        rows = df.values.tolist()
        return columns, rows

class GCSConnector(DataSourceConnector):
    def connect(self):
        try:
            self.connection = storage.Client.from_service_account_json(self.config['key_file'])
            print("[SUCCESS] GCS connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] GCS connection failed:", str(e))
            return None

    def get_data(self, bucket_name, blob_name):
        bucket = self.connection.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        data = blob.download_as_text()
        from io import StringIO
        df = pd.read_csv(StringIO(data))
        columns = list(df.columns)
        rows = df.values.tolist()
        return columns, rows

class APIConnector(DataSourceConnector):
    def get_data(self, url, headers=None, params=None):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            # Assume list of dicts
            if isinstance(data, list) and data:
                columns = list(data[0].keys())
                rows = [list(item.values()) for item in data]
                return columns, rows
        return [], []

class DatabricksConnector(DataSourceConnector):
    def connect(self):
        if sql is None:
            print("[ERROR] databricks-sql-connector not installed")
            print("[INFO] Install with: pip install databricks-sql-connector")
            return None
        try:
            workspace_url = self.config.get('workspace_url', '')
            # Remove https:// prefix if present
            server_hostname = workspace_url.replace('https://', '').replace('http://', '')
            http_path = self.config.get('http_path')
            auth_type = self.config.get('auth_type', 'token')
            
            print(f"[DEBUG] Databricks connection: workspace={server_hostname}, auth={auth_type}")
            
            if auth_type == 'token':
                # Personal Access Token authentication
                access_token = self.config.get('access_token')
                if not access_token:
                    print("[ERROR] Access token is required for token authentication")
                    return None
                
                self.connection = sql.connect(
                    server_hostname=server_hostname,
                    http_path=http_path,
                    access_token=access_token
                )
                
            elif auth_type == 'azure_ad_interactive':
                # Azure AD Interactive (OAuth with browser MFA)
                azure_tenant_id = self.config.get('azure_tenant_id')
                azure_client_id = self.config.get('azure_client_id')
                
                if not azure_tenant_id or not azure_client_id:
                    print("[ERROR] Azure Tenant ID and Client ID are required for Azure AD Interactive authentication")
                    return None
                
                # Use Azure Active Directory OAuth U2M (User to Machine) authentication
                # This will trigger browser-based OAuth flow with MFA support
                self.connection = sql.connect(
                    server_hostname=server_hostname,
                    http_path=http_path,
                    auth_type='databricks-oauth',  # OAuth U2M for interactive browser login
                    # Note: databricks-oauth will automatically handle the browser-based OAuth flow
                )
                
            elif auth_type == 'azure_ad_service_principal':
                # Azure AD Service Principal authentication
                azure_tenant_id = self.config.get('azure_tenant_id')
                azure_client_id = self.config.get('azure_client_id')
                azure_client_secret = self.config.get('azure_client_secret')
                
                if not all([azure_tenant_id, azure_client_id, azure_client_secret]):
                    print("[ERROR] Azure Tenant ID, Client ID, and Client Secret are required for Service Principal authentication")
                    return None
                
                # Use Azure AD Service Principal (M2M - Machine to Machine) authentication
                self.connection = sql.connect(
                    server_hostname=server_hostname,
                    http_path=http_path,
                    auth_type='azure-service-principal',
                    azure_tenant_id=azure_tenant_id,
                    azure_client_id=azure_client_id,
                    azure_client_secret=azure_client_secret
                )
            else:
                print(f"[ERROR] Unknown authentication type: {auth_type}")
                return None
            
            # Set catalog and schema if provided
            catalog = self.config.get('catalog')
            schema = self.config.get('schema')
            if catalog and schema:
                cursor = self.connection.cursor()
                cursor.execute(f"USE CATALOG {catalog}")
                cursor.execute(f"USE SCHEMA {schema}")
                cursor.close()
                print(f"[SUCCESS] Using catalog: {catalog}, schema: {schema}")
            
            print("[SUCCESS] Databricks connection established.")
            return self.connection
        except Exception as e:
            print("[ERROR] Databricks connection failed:", str(e))
            import traceback
            traceback.print_exc()
            return None

    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def get_data(self, query):
        cursor = self.execute_query(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

class PowerBIConnector(DataSourceConnector):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.tenant_id = config.get('tenant_id')
        self.access_token = None
        self.token_expires = None

    def _get_access_token(self):
        """Get OAuth2 access token for Power BI"""
        import requests
        from datetime import datetime, timedelta

        # Check if we have a valid token
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token

        # Get new token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://analysis.windows.net/powerbi/api/.default'
        }

        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Token expires in about 1 hour, set expiry to 50 minutes from now
            self.token_expires = datetime.now() + timedelta(minutes=50)
            return self.access_token
        else:
            raise Exception(f"Failed to get Power BI access token: {response.text}")

    def _get_headers(self):
        """Get headers with valid access token"""
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_datasets(self):
        url = f"{self.base_url}/datasets"
        response = requests.get(url, headers=self._get_headers())
        return response.json() if response.status_code == 200 else None

    def get_dataflows(self):
        url = f"{self.base_url}/dataflows"
        response = requests.get(url, headers=self._get_headers())
        return response.json() if response.status_code == 200 else None

    def execute_dax_query(self, dataset_id, dax_query):
        url = f"{self.base_url}/datasets/{dataset_id}/executeQueries"
        payload = {"queries": [{"query": dax_query}]}
        response = requests.post(url, headers=self._get_headers(), json=payload)
        return response.json() if response.status_code == 200 else None

    def get_reports(self):
        url = f"{self.base_url}/reports"
        response = requests.get(url, headers=self._get_headers())
        return response.json() if response.status_code == 200 else None

    def get_workspaces(self):
        url = f"{self.base_url}/groups"
        response = requests.get(url, headers=self._get_headers())
        return response.json() if response.status_code == 200 else None

    def get_dataset_tables(self, dataset_id):
        url = f"{self.base_url}/datasets/{dataset_id}/tables"
        response = requests.get(url, headers=self._get_headers())
        return response.json() if response.status_code == 200 else None

    def get_dataset_measures(self, dataset_id):
        url = f"{self.base_url}/datasets/{dataset_id}/measures"
        response = requests.get(url, headers=self._get_headers())
        return response.json() if response.status_code == 200 else None

    def validate_dax_expression(self, dataset_id, dax_expression):
        # Use executeQueries to validate DAX
        result = self.execute_dax_query(dataset_id, f"EVALUATE {dax_expression}")
        return result is not None and 'error' not in result

    def get_report_pages(self, report_id):
        url = f"{self.base_url}/reports/{report_id}/pages"
        response = requests.get(url, headers=self._get_headers())
        return response.json() if response.status_code == 200 else None

    def get_visuals_on_page(self, report_id, page_name):
        url = f"{self.base_url}/reports/{report_id}/pages/{page_name}"
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            page_data = response.json()
            return page_data.get('visuals', [])
        return []

def load_data_source_config(source_name='default'):
    config_path = os.path.join(os.path.dirname(__file__), 'data_sources.json')
    with open(config_path, 'r') as f:
        configs = json.load(f)

    config = configs.get(source_name, configs['default'])

    # For Power BI, override with environment variables for security
    if config.get('type') == 'powerbi':
        from config.secrets import POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID
        config['client_id'] = POWERBI_CLIENT_ID or config.get('client_id')
        config['client_secret'] = POWERBI_CLIENT_SECRET or config.get('client_secret')
        config['tenant_id'] = POWERBI_TENANT_ID or config.get('tenant_id')

    return config

def create_connection(source_name='default'):
    config = load_data_source_config(source_name)
    connector_type = config.get('type')
    if connector_type == 'sqlserver':
        connector = SQLServerConnector(config)
    elif connector_type == 'azuresynapse':
        connector = AzureSynapseConnector(config)
    elif connector_type == 'fabric':
        connector = MicrosoftFabricConnector(config)
    elif connector_type == 'mysql':
        connector = MySQLConnector(config)
    elif connector_type == 'postgresql':
        connector = PostgreSQLConnector(config)
    elif connector_type == 'oracle':
        connector = OracleConnector(config)
    elif connector_type == 'mongodb':
        connector = MongoDBConnector(config)
    elif connector_type == 'cassandra':
        connector = CassandraConnector(config)
    elif connector_type == 'dynamodb':
        connector = DynamoDBConnector(config)
    elif connector_type == 'file':
        connector = FileConnector(config)
    elif connector_type == 's3':
        connector = S3Connector(config)
    elif connector_type == 'azureblob':
        connector = AzureBlobConnector(config)
    elif connector_type == 'gcs':
        connector = GCSConnector(config)
    elif connector_type == 'api':
        connector = APIConnector(config)
    elif connector_type == 'powerbi':
        connector = PowerBIConnector(config)
    elif connector_type == 'databricks':
        connector = DatabricksConnector(config)
    else:
        raise ValueError(f"Unsupported connector type: {connector_type}")

    return connector.connect()
