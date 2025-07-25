from typing import List
from typing import Optional

from pymongo.operations import SearchIndexModel

from src.mongodb.atlas import get_mongo_client


class MongoManager:
    def __init__(self):
        # self.client = ConnectionManager("mongodb").get_connection()
        self.client = get_mongo_client()

    def get_or_create_collection(
        self,
        collection_name: str,
        db_name: Optional[str] = 'test',
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

    def list_collections(self, db_name: Optional[str] = 'test') -> List[str]:
        """
        List all collections under <db_name>

        :param db_name: Database name default [test]
        """
        db = self.client[db_name]
        collections = db.list_collection_names()
        return collections

    def delete_collection(self, collection_name: str, db_name: Optional[str] = 'test'):
        db = self.client[db_name]
        db[collection_name].drop()