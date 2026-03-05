from domain.ports import DocumentStorePort
from infrastructure.redis.redis_client import save_document_version_name,get_document_version_name,save_document_hash,get_document_hash
from infrastructure.redis.redis_config import get_redis_client

class RedisDocumentStore(DocumentStorePort):
    def __init__(self):
        self.redis = get_redis_client()

    def save_document_version_name(self, updated_name: str) -> bool:
        return save_document_version_name(updated_name)

    def get_document_version_name(self) -> str:
        return get_document_version_name()

    def save_document_hash(self, document_id: str, document_hash: str) -> bool:
        return save_document_hash(document_id, document_hash)

    def get_document_hash(self, document_id: str) -> str:
        return get_document_hash(document_id)