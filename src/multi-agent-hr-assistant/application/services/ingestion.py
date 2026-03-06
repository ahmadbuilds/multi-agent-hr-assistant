from hashlib import sha256
from datetime import datetime
from typing import Literal
from langchain_text_splitters import RecursiveCharacterTextSplitter
from domain.ports import DocumentStorePort,VectorStorePort
import re
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
            if not document_id or document_id=="":
                print("No document version name found in Redis. Assuming document has changed.")
                return "no_policy"
            #get the stored hash from redis
            stored_hash = self.redis_store.get_document_hash(document_id)
            if not stored_hash or stored_hash=="":
                print("No document hash found in Redis. Assuming document has changed.")
                return "no_policy"
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
            ids=[]
            for i in range(len(chunks)):
                chunk_hash=self.hash_function(chunks[i])
                ids.append(chunk_hash)
                metadatas.append({
                    "policy_name":"HR Policy",
                    "uploaded_by":"admin",
                    "chunk_hash":chunk_hash,
                    "document_hash":doc_hash,
                    "upload_date":datetime.now().isoformat(),
                })
            
            #upsert the chunks and metadata into the vector store
            if not self.vector_store.upsert_embeddings(chunks,metadatas,ids):
                print("Error upserting embeddings into vector store.")
                return False
            
            #save the document version name in Redis
            document_id=self.redis_store.get_document_version_name()
            if not document_id or document_id=="":
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
            
    #function to update the existing policy document by splitting it into chunks, generating embeddings and storing them in the vector store and updating the document hash in Redis
    def handle_policy_update(self,document_content:str)->bool:
        """
        Handle the update of an existing policy document by splitting it into chunks, generating embeddings, and storing them in the vector store. Also updates the document hash in Redis.
        args:
            document_content (str): The content of the policy document to be updated.
        returns:
            bool: True if the update is successful, False otherwise.
        """
        try:
            #splitting the new document into chunks and generating the new document hash
            new_doc_hash=self.hash_function(document_content)
            new_chunks=self.split_text(document_content)

            #generate metadata for each new chunk
            new_metadatas=[]
            new_ids=[]
            for i in range(len(new_chunks)):
                chunk_hash=self.hash_function(new_chunks[i])
                new_ids.append(chunk_hash)
                new_metadatas.append({
                    "policy_name":"HR Policy",
                    "uploaded_by":"admin",
                    "chunk_hash":chunk_hash,
                    "document_hash":new_doc_hash,
                    "upload_date":datetime.now().isoformat(),
                })

            #getting the old document version name and hash from Redis
            document_id=self.redis_store.get_document_version_name()
            if not document_id or document_id=="":
                print("No existing document version found in Redis. Cannot update non-existing document.")
                return False
            
            old_doc_hash=self.redis_store.get_document_hash(document_id)
            if not old_doc_hash or old_doc_hash=="":
                print("No existing document hash found in Redis. Cannot update non-existing document.")
                return False
            
            #getting the chunk hashes of the old document from the vector store
            new_chunk_hashes=set([metadata["chunk_hash"] for metadata in new_metadatas])
            existing_chunk_hashes=set(self.vector_store.get_existing_chunk_hashes(old_doc_hash))


            #Chunks to add are the ones which are in new document but not in existing document
            hashes_to_add=new_chunk_hashes-existing_chunk_hashes
            for i in range(len(new_metadatas)):
                if new_metadatas[i]["chunk_hash"] in hashes_to_add:
                    if not self.vector_store.upsert_embeddings([new_chunks[i]],[new_metadatas[i]],[new_ids[i]]):
                        print("Error upserting new chunk into vector store.")
                        return False
                    
            #Chunks to delete are the ones which are in existing document but not in new document
            hashes_to_delete=existing_chunk_hashes-new_chunk_hashes
            
            #first remove the previous document hash from Redis to avoid any conflict during deletion of old chunks
            if not self.redis_store.delete_document_hash(document_id):
                print("Error deleting old document hash from Redis.")
                return False
            
            #saving the new document hash into Redis and also updating the document id
            #updating only the same number in the string of the document version to maintain the same document id for the updated document
            match=re.search(r'v(\d+)$', document_id)
            if match:
                version_number=int(match.group(1))
                new_version_number=version_number+1
                new_document_id=re.sub(r'v\d+$', f'v{new_version_number}', document_id)
            else:
                new_document_id=document_id
             
            if not self.redis_store.save_document_hash(new_document_id,new_doc_hash):
                print("Error saving new document hash in Redis.")
                return False
            
            #updating the document hash which are not to be deleted with the new document hash to maintain the same document hash for the unchanged chunks
            for chunk_hash in existing_chunk_hashes:
                if chunk_hash not in hashes_to_delete:
                    #fetch the metadata of the chunk to be updated from the vector store
                    result = self.vector_store.get(where={"chunk_hash":chunk_hash},include=["metadatas","ids","documents","embeddings"])
                    if result and "metadatas" in result and result["metadatas"]:
                        metadata=result["metadatas"][0]
                        metadata["document_hash"]=new_doc_hash
                        #upsert the chunk with the updated document hash into the vector store
                        if not self.vector_store.upsert_embeddings([result["documents"][0]],[metadata],[result["ids"][0]]):
                            print("Error upserting existing chunk with new document hash into vector store.")
                            return False
            
            #deleting the chunks which are not in the new document from the vector store
            for chunk_hash in hashes_to_delete:
                if not self.vector_store.delete_chunks_by_chunk_hash(chunk_hash):
                    print("Error deleting old chunk from vector store.")
                    return False
            
            #updating the document version name in Redis to the new document id
            if not self.redis_store.save_document_version_name(new_document_id):
                print("Error updating document version name in Redis.")
                return False
            
            return True
        except Exception as e:
            print(f"Error handling policy update: {e}")
            return False