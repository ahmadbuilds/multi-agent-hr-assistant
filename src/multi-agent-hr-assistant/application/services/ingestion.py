from hashlib import sha256
from datetime import datetime
from typing import Literal
from langchain_text_splitters import RecursiveCharacterTextSplitter
from domain.ports import DocumentStorePort,VectorStorePort
#Implementing the Abstract function
class IngestionService:
    def __init__(self,redis_store:DocumentStorePort,vector_store:VectorStorePort):
        self.redis_store = redis_store
        self.vector_store = vector_store

    #function to hash the text
    def hash_function(self, text:str)->str:
        """
        Generate SHA256 hash for the given text.
        args:
            text (str): The input text to be hashed.
        returns:
            str: The SHA256 hash of the input text.
        """
        return sha256(text.encode(str="utf-8")).hexdigest()

    #function to split the text into chunks
    def split_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
        """
        Split the given text into chunks of specified size with overlap.
        args:
            text (str): The text to be split.
            chunk_size (int): The size of each chunk. Default is 1000 characters.
            chunk_overlap (int): The overlap between chunks. Default is 200 characters.
        returns:
            list: A list of text chunks.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return splitter.split_text(text)
    
    #function to check if the document has changed by comparing the hash of the new document with the stored hash in Redis
    def has_document_changed(self,document_content:str) -> Literal["no_policy","unchanged","changed"]:
        """
        Check if the document has changed by comparing the hash of the new document with the stored hash in Redis.
        args:
            document_content (str): The content of the policy document to be checked.
        returns:    
            Literal["no_policy","unchanged","changed"]: "no_policy" if no document is found in Redis, "unchanged" if the document has not changed, "changed" if the document has changed.
        """
        try:
            #get the document version name from redis
            document_id=self.redis_store.get_document_version_name()
            if not document_id:
                print("No document version name found in Redis. Assuming document has changed.")
                return "no_policy"
            #get the stored hash from redis
            stored_hash = self.redis_store.get_document_hash(document_id)
            #generate the hash of the new document
            new_hash = self.hash_function(document_content)
            #compare the hashes
            return "changed" if new_hash != stored_hash else "unchanged"
        except Exception as e:
            print(f"Error checking document change: {e}")
            return "changed"
    
    #function to ingest the document by splitting it into chunks, generating embeddings and storing them in the vector store and saving the document hash in Redis
    def handle_new_policy_upload(self,document_content:str)->bool:
        """
        Handle the ingestion of a new policy document by splitting it into chunks, generating embeddings, and storing them in the vector store. Also saves the document hash in Redis.        
        args:
            document_content (str): The content of the policy document to be ingested.
        returns:
            bool: True if the ingestion is successful, False otherwise.
        """
        try:
            #split the document into chunks
            chunks=self.split_text(document_content)
            doc_hash=self.hash_function(document_content)

            #generate metadata for each chunk
            metadatas=[]
            for i in range(len(chunks)):
                metadatas.append({
                    "policy_id":1,
                    "policy_name":"HR Policy",
                    "uploaded_by":"admin",
                    "chunk_hash":self.hash_function(chunks[i]),
                    "document_hash":doc_hash,
                    "upload_date":datetime.now().isoformat(),
                })
            
            #upsert the chunks and metadata into the vector store
            if not self.vector_store.upsert_embeddings(chunks,metadatas):
                print("Error upserting embeddings into vector store.")
                return False
            
            #save the document version name in Redis
            document_id=self.redis_store.get_document_version_name()
            if not document_id:
                document_id=f"document_version_v1"
                self.redis_store.save_document_version_name(document_id)
            
            #saving the document hash into redis
            if not self.redis_store.save_document_hash(document_id,doc_hash):
                print("Error saving document hash in Redis.")
                return False
            
            return True
        except Exception as e:
            print(f"Error handling new policy upload: {e}")
            return False
            
    