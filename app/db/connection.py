"""
Simple BigQuery connection for service_account.json
"""

import os
from langchain_community.utilities import SQLDatabase
from google.cloud import bigquery
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)

class BigQueryConnection:
    def __init__(self):
        self.client = None
        self.db = None
        self.project_id = None
        self.dataset_id = None
        self.credentials = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup BigQuery connection using service_account.json"""
        try:
            self.project_id = os.getenv("BIGQUERY_PROJECT_ID")
            self.dataset_id = os.getenv("BIGQUERY_DATASET")
            
            if not self.project_id:
                raise ValueError("BIGQUERY_PROJECT_ID environment variable required")
            if not self.dataset_id:
                raise ValueError("BIGQUERY_DATASET environment variable required")
            
            # Use service_account.json from project root
            credentials_path = os.path.abspath("service_account.json")
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"service_account.json file not found at: {credentials_path}")
            
            # Setup credentials
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
            
            # Initialize BigQuery client
            self.client = bigquery.Client(project=self.project_id, credentials=self.credentials)
            
            # Create SQLDatabase for LangChain with explicit credentials
            # Use a simpler connection URI and pass credentials via environment
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            connection_uri = f"bigquery://{self.project_id}/{self.dataset_id}"
            
            try:
                self.db = SQLDatabase.from_uri(connection_uri)
            except Exception as e:
                logger.warning(f"SQLDatabase connection failed: {e}")
                logger.info("Proceeding with native BigQuery client only")
                self.db = None
            
            logger.info(f"✅ Connected to BigQuery project: {self.project_id}")
            logger.info(f"📊 Using dataset: {self.dataset_id}")
            
            # Test the connection and list available tables
            self._list_available_tables()
            
        except Exception as e:
            logger.error(f"❌ BigQuery connection failed: {str(e)}")
            raise
    
    def _list_available_tables(self):
        """List and log available tables in the dataset"""
        try:
            dataset_ref = self.client.dataset(self.dataset_id, project=self.project_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            if tables:
                table_names = [table.table_id for table in tables]
                logger.info(f"📋 Available tables in {self.dataset_id}: {', '.join(table_names[:10])}")
                if len(table_names) > 10:
                    logger.info(f"   ... and {len(table_names) - 10} more tables")
            else:
                logger.warning(f"⚠️ No tables found in dataset {self.dataset_id}")
                
        except Exception as e:
            logger.warning(f"Could not list tables: {str(e)}")
    
    def get_schema_info(self):
        """Get complete schema information including tables and columns"""
        try:
            dataset_ref = self.client.dataset(self.dataset_id, project=self.project_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            schema_info = {}
            for table in tables:
                table_ref = dataset_ref.table(table.table_id)
                table_obj = self.client.get_table(table_ref)
                
                columns = []
                for field in table_obj.schema:
                    column_info = {
                        'name': field.name,
                        'type': field.field_type,
                        'description': field.description or ''
                    }
                    columns.append(column_info)
                
                schema_info[table.table_id] = {
                    'columns': columns,
                    'num_rows': table_obj.num_rows,
                    'description': table_obj.description or ''
                }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {str(e)}")
            return {}
    
    def get_db(self):
        return self.db
    
    def get_client(self):
        return self.client
    
    def test_connection(self):
        try:
            query = "SELECT 1 as test"
            list(self.client.query(query).result())
            return True
        except:
            return False
    
    def get_dataset_info(self):
        """Get information about the current dataset"""
        return {
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "full_dataset": f"{self.project_id}.{self.dataset_id}"
        }

# Global instance
_connection = None

def get_db_connection():
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_db()

def get_bigquery_client():
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_client()

def get_dataset_info():
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_dataset_info()

def get_schema_info():
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_schema_info() 