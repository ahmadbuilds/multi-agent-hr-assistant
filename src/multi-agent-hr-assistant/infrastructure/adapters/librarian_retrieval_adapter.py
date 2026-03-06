from domain.ports import LibrarianRetrievalPort
from infrastructure.vector_store.chroma_client import create_chroma_instance

class LibrarianRetrievalAdapter(LibrarianRetrievalPort):
    def __init__(self):
        self.vector_store_client = create_chroma_instance()

    def retrieve_document(self, query: str) -> list[str]:
        """
        Method to retrieve relevant document based on the user query
        Args:
            query (str): User query for which to retrieve the relevant document
        Returns:
            list[str]: List of contents of the retrieved documents
        """
        try:
            #query the vector store to get the most relevant document based on the user query
            results = self.vector_store_client.similarity_search(query, k=3)
            if results and len(results) > 0:
                return [result.page_content for result in results]
            else:
                print("No relevant document found for the query.")
                return ["No relevant document found."]
        except Exception as e:
            print("Error retrieving document from vector store:", str(e))
            return ["Error retrieving document."]