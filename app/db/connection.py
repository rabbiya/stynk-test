"""
BigQuery Database Connection
Handles connection to BigQuery and provides schema information
"""

import os
from langchain_community.utilities import SQLDatabase
from google.cloud import bigquery
from google.oauth2 import service_account
import logging
from app.db.schema_metadata import SCHEMA_DESCRIPTIONS

logger = logging.getLogger(__name__)

# Debug check for schema metadata
logger.info(f"Available tables in SCHEMA_DESCRIPTIONS: {list(SCHEMA_DESCRIPTIONS.keys())}")

class BigQueryConnection:
    """Manages BigQuery connection and schema information"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.project_id = None
        self.dataset_id = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Initialize BigQuery connection using service account"""
        try:
            # Get project and dataset from environment
            self.project_id = os.getenv("BIGQUERY_PROJECT_ID")
            self.dataset_id = os.getenv("BIGQUERY_DATASET")
            
            if not self.project_id or not self.dataset_id:
                raise ValueError("Missing BIGQUERY_PROJECT_ID or BIGQUERY_DATASET environment variables")
            
            # Load service account credentials
            credentials_path = os.path.abspath("service_account.json")
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"service_account.json not found at: {credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            
            # Initialize BigQuery client
            self.client = bigquery.Client(project=self.project_id, credentials=credentials)
            
            # Setup LangChain SQLDatabase (optional, for compatibility)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            connection_uri = f"bigquery://{self.project_id}/{self.dataset_id}"
            
            try:
                self.db = SQLDatabase.from_uri(connection_uri)
            except Exception as e:
                logger.warning(f"SQLDatabase setup failed: {e}")
                self.db = None
            
            logger.info(f"✅ Connected to BigQuery: {self.project_id}.{self.dataset_id}")
            self._log_available_tables()
            
        except Exception as e:
            logger.error(f"❌ BigQuery connection failed: {str(e)}")
            raise
    
    def _log_available_tables(self):
        """Log available tables for debugging"""
        try:
            dataset_ref = self.client.dataset(self.dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            table_names = [table.table_id for table in tables]
            
            if table_names:
                logger.info(f"📋 Found {len(table_names)} tables: {', '.join(table_names[:5])}")
                if len(table_names) > 5:
                    logger.info(f"    ... and {len(table_names) - 5} more")
            else:
                logger.warning(f"⚠️ No tables found in {self.dataset_id}")
                
        except Exception as e:
            logger.warning(f"Could not list tables: {e}")
    
    def get_schema_info(self):
        """Get complete schema information for all tables"""
        try:
            dataset_ref = self.client.dataset(self.dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            schema_info = {}
            for table in tables:
                table_id = table.table_id
                table_ref = dataset_ref.table(table_id)
                table_obj = self.client.get_table(table_ref)
                
                # Get metadata descriptions from schema_metadata
                table_metadata = SCHEMA_DESCRIPTIONS.get(table_id, {})
                logger.info(f"Table {table_id} metadata: {table_metadata}")
                
                table_desc = table_metadata.get('description', '') or table_obj.description or ''
                logger.info(f"Table {table_id} description: {table_desc}")
                
                column_metadata = {col['name']: col for col in table_metadata.get('columns', [])} if table_metadata else {}
                logger.info(f"Table {table_id} column metadata: {column_metadata}")
                
                # Extract column information
                columns = []
                for field in table_obj.schema:
                    # Get column metadata if available
                    col_metadata = column_metadata.get(field.name, {})
                    logger.info(f"Column {field.name} metadata: {col_metadata}")
                    
                    description = col_metadata.get('description', '') or field.description or ''
                    logger.info(f"Column {field.name} description: {description}")
                    
                    columns.append({
                        'name': field.name,
                        'type': field.field_type,
                        'description': description
                    })
                
                # Store table information
                schema_info[table_id] = {
                    'columns': columns,
                    'num_rows': table_obj.num_rows,
                    'description': table_desc
                }
                
                logger.info(f"Final schema info for table {table_id}: {schema_info[table_id]}")
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return {}
    
    def get_db(self):
        """Get LangChain SQLDatabase instance"""
        return self.db
    
    def get_client(self):
        """Get BigQuery client instance"""
        return self.client
    
    def get_dataset_info(self):
        """Get dataset information"""
        return {
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "full_dataset": f"{self.project_id}.{self.dataset_id}"
        }

# Global connection instance (singleton pattern)
_connection = None

def get_db_connection():
    """Get or create database connection"""
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_db()

def get_bigquery_client():
    """Get or create BigQuery client"""
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_client()

def get_dataset_info():
    """Get dataset information"""
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_dataset_info()

def get_schema_info():
    """Get schema information for all tables"""
    global _connection
    if _connection is None:
        _connection = BigQueryConnection()
    return _connection.get_schema_info() 