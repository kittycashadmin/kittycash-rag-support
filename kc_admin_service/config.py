# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

APP_HOST = "0.0.0.0"
APP_PORT = 9008
DATABASE_URL = "postgresql://postgres:password@kittycash_db:5432/mydb"
REDIS_URL = "redis://redis:6379/0"
RETRIEVER_URL = "http://retrieval_service:9004"
INDEXER_URL = "http://data_indexing_service:9003"
API_SERVER_URL = "http://api_server:9006"
TOP_K = 3
MAX_BULK_IDS = 200