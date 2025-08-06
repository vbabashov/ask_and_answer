from typing import Optional
from typing import List
from typing import Dict
from typing import Any


from pymongo.operations import SearchIndexModel

from utils.tools.mongodb.atlas import get_mongo_client
from embeddings import aoai_embed_query

from dotenv import load_dotenv
load_dotenv()

class MongoManager:
    def __init__(self):
        # self.client = ConnectionManager("mongodb").get_connection()
        self.client = get_mongo_client()

    def get_or_create_collection(
            self, collection_name: str, db_name: Optional[str] = "test"
        ):
            """
            Get or create a collection with the given name.

            :param collection_name: The name of the collection to create.
            :param db_name: Name of the database. Default is 'test'
            :return: The created collection.
            """
            db = self.client[db_name]
            collection = db[collection_name]
            return collection

    def list_search_indexes(
        self, collection_name: str, db_name: Optional[str] = "test"
    ):
        """
        List the search indexes of a collection.

        :param collection_name: The name of the collection to list the search indexes.
        :param db_name: Name of the database. Default is 'test'
        :return: The list of search indexes.
        """
        collection = self.client[db_name][collection_name]
        search_indexes = collection.list_search_indexes()
        return search_indexes

    def create_search_index(
        self,
        collection_name: str,
        index_name: str,
        dimensions: int,
        path: str,
        similarity: str,
        db_name: Optional[str] = "test",
    ) -> str:
        """
        Create a search index in a collection.

        :param collection_name: The name of the collection to create the search index.
        :param index_name: Name of the index to be created.
        :param dimensions: Number of vector dimensions. Value can be between 1 and 4096, both inclusive.
        :param search_index_model: The search index model to create the search index.
        :param path: Name of the field to index. Use dot notation for embedded fields.
        :param similarity: Vector similarity function to use to search for top K-nearest neighbors.
        :param db_name: Name of the database. Default is 'test'
        :return: The name of the new search index.
        """
        collection = self.client[db_name][collection_name]

        vector_search_index_model = self.__create_search_index_model(
            index_name=index_name,
            dimensions=dimensions,
            similarity=similarity,
            path=path,
        )

        vector_search_indexes = self.list_search_indexes(
            collection_name=collection_name
        )

        if index_name in [idx["name"] for idx in vector_search_indexes]:
            return print(
                f"Search index {index_name} already exists in collection {collection_name}"
            )

        index_name = collection.create_search_index(model=vector_search_index_model)
        return index_name

    def __create_search_index_model(
        self, index_name: str, dimensions: int, similarity: str, path: str
    ):
        """
        Create a search index model.

        :param index_name: The name of the search index.
        :param dimensions: Number of vector dimensions. Value can be between 1 and 4096, both inclusive.
        :param similarity: Vector similarity function to use to search for top K-nearest neighbors.

            Values include:

            euclidean - measures the distance between ends of vectors allowing similarity measurements based on varying dimensions.
            cosine - measures similarity based on the angle between vectors allowing for similarity measurements not scaled by magnitude.
            dotProduct - measures similarity based on both the angle between, and magnitude of vectors.

        :param path: Name of the field to index. Use dot notation for embedded fields.
        :return: The search index model.
        """
        search_index_model = SearchIndexModel(
            definition={
                "dynamic": True,
                "fields": [
                    {
                        "type": "vector",
                        "numDimensions": dimensions,
                        "similarity": similarity,
                        "path": path,
                    }
                ],
            },
            name=index_name,
            type="vectorSearch",
        )

        return search_index_model

    def delete_search_index(
        self, collection_name: str, index_name: str, db_name: Optional[str] = "test"
    ):
        """
        Delete a search index from a collection.

        :param collection_name: The name of the collection to delete the search index.
        :param index_name: The name of the search index to delete.
        :param db_name: Name of the database. Default is 'test'.
        """
        collection = self.client[db_name][collection_name]

        vector_search_indexes = self.list_search_indexes(
            collection_name=collection_name
        )
        if index_name not in [idx["name"] for idx in vector_search_indexes]:
            print(
                f"Search index {index_name} does not exist in collection {collection_name}"
            )
            return

        collection.drop_search_index(index_name)

    def retrieve_documents(
        self,
        embedded_query: str,
        search_index_name: str,
        search_column: str,
        collection_name,
        db_name,
    ):
        """
        Retrieve documents from MongoDB

        :param query: Search query
        :param client: Azure OpenAI Client
        :param search_index_name: Index name
        :param search_column: Search Column (embedding columns)
        :param collection: Collection with the embedded field.
        :return: results
        """
        collection = self.get_or_create_collection(
            collection_name=collection_name, db_name=db_name
        )
        search_pipeline = self._get_search_pipeline(
            search_index_name=search_index_name,
            search_column=search_column,
            embedded_query=embedded_query,
        )
        results = collection.aggregate(pipeline=search_pipeline)
        return results

    def list_collections(self, db_name: Optional[str] = "test") -> List[str]:
        """
        List all collections under <db_name>

        :param db_name: Database name default [test]
        """
        db = self.client[db_name]
        collections = db.list_collection_names()
        return collections

    def _get_search_pipeline(
        self, search_index_name: str, search_column: str, embedded_query: List[float]
    ) -> List[Dict[str, Any]]:
        """
        Pipeline for vector search.

        :param search_index_name: Name for the search index.
        :param search_column: Column with the embeddings.
        :param embedded_query: The embedding vector for the query.
        :return: Pipeline
        """
        pipeline = [
            {
                "$vectorSearch": {
                    "index": search_index_name,
                    "path": search_column,
                    "queryVector": embedded_query,
                    "limit": 2,
                    "numCandidates": 50,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        return pipeline

    def add_content(
        self, collection, content, embedded_content: List[float], filename: str
    ) -> None:
        """
        Inserts a document in mongodb with the respective embedding vector.

        :param collection: Collection object with the search column
        :param content: File content.
        :param embedded_content: Embedding Vector for the content.
        :param filename: Name of the file
        """

        document = {
            "filename": filename,
            "content": content.decode("utf-8"),
            "embedding": embedded_content,
        }

        result = collection.insert_one(document)
        if result.acknowledged:
            print(f"Document inserted with _id: {result.inserted_id}")
        else:
            print("Document insertion failed.")

   # https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/
    def perform_vector_search(self, collection_name, index_name, attr_name, prompt=None, projection: list = [], limit=3):
        collection = self.database[collection_name]
        if prompt is None:
            raise ValueError("Prompt is required")
    
        embedding_vector = aoai_embed_query(prompt)
        projected_fields = dict(score= { "$meta": 'vectorSearchScore' })
        if len(projection) != 0:
            for field in projection:
                projected_fields[field] = 1 # type: ignore
        else:
            projected_fields["document"] = '$$ROOT' # type: ignore

        print(f"Projected fields: {projected_fields}")

        pipeline = [
                {
                    "$vectorSearch": {
                        "index": index_name,
                        "queryVector": embedding_vector,
                        "path": attr_name,
                        "limit": limit,
                        "exact": True
                    }
                },
                {
                    "$project": projected_fields
                }
            ]
        results = collection.aggregate(pipeline)
        return list(results)