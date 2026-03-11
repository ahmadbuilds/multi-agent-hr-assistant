from domain.ports import LibrarianRetrievalPort,LibrarianInsertionPort,LibrarianUpdatePort
from langchain.tools import tool

def make_librarian_retrieval_tool(retrieval_port:LibrarianRetrievalPort):
    @tool("librarian_retrieval_tool", description="Tool for the Librarian Agent to retrieve relevant document based on the user query.")
    def librarian_retrieval_tool(query:str)->str:
        """
        Tool for the Librarian Agent to retrieve relevant document based on the user query
        Args:
            query (str): User query for which to retrieve the relevant document
        Returns:
            list[str]: Content of the retrieved document
        """
        return retrieval_port.retrieve_document(query)
    return librarian_retrieval_tool

def make_librarian_update_tool(update_port:LibrarianUpdatePort):
    @tool("librarian_update_tool", description="Tool for the Librarian Agent to update an existing document based on the provided content.")
    def librarian_update_tool(document_content:str)->bool:
        """
        Tool for the Librarian Agent to update an existing document based on the provided content
        Args:
            document_content (str): Content of the document to be updated
        Returns:
            bool: True if document update is successful, False otherwise
        """
        return update_port.update_document(document_content)
    return librarian_update_tool

def make_librarian_insertion_tool(insertion_port:LibrarianInsertionPort):
    @tool("librarian_insertion_tool", description="Tool for the Librarian Agent to insert a new document based on the provided content.")
    def librarian_insertion_tool(document_content:str)->bool:
        """
        Tool for the Librarian Agent to insert a new document based on the provided content
        Args:
            document_content (str): Content of the document to be inserted
        Returns:
            bool: True if document insertion is successful, False otherwise
        """
        return insertion_port.insert_document(document_content)
    return librarian_insertion_tool