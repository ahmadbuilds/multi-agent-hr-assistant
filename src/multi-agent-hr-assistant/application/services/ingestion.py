from domain.ports import IDocumentIngestor
from hashlib import sha256
from datetime import datetime
from supabase import create_client, Client

#Implementing the Abstract function
class DocumentIngestor(IDocumentIngestor):

    #function to hash the text
    def has_function(self, text:str)->str:
        """
        Generate SHA256 hash for the given text.
        """
        return sha256(text.encode(str="utf-8")).hexdigest()

        
