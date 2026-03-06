from domain.ports import DocumentStorePort
from infrastructure.redis.redis_client import save_document_version,get_document_version,save_document_hash_to_redis,get_document_hash_to_redis,delete_document_hash_to_redis
from infrastructure.redis.redis_config import get_redis_client

class RedisDocumentStore(DocumentStorePort):
    def __init__(self):
        self.redis = get_redis_client()

    def save_document_version_name(self, updated_name: str) -> bool:
        return save_document_version(updated_name)

    def get_document_version_name(self) -> str:
        return get_document_version()

    def save_document_hash(self, document_id: str, document_hash: str) -> bool:
        return save_document_hash_to_redis(document_id, document_hash)

    def get_document_hash(self, document_id: str) -> str:
        return get_document_hash_to_redis(document_id)

    def delete_document_hash(self, document_id: str) -> bool:
        return delete_document_hash_to_redis(document_id)