from typing import List
import os

def aoai_embed_query(query: str, client) -> List[float]:
    """
    generate a vector embedding of the user's question

    :param query: Search query
    :param client: Azure OpenAI Client
    :return: Embedded query
    """

    embedding = client.embeddings.create(
        input=query, model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    )
    embedded_query = embedding.data[0].embedding
    return embedded_query