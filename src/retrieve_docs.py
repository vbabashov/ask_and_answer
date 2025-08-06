from dotenv import load_dotenv
load_dotenv()

from utils.tools.mongodb.atlas_mongo_util import MongoManager
from utils.tools.mongodb.atlas import get_mongo_client
from embeddings import aoai_embed_query
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import os


def main():

    # Initialize MongoDB client
    mongo = MongoManager()

    user_message = "What type of the espresso machine do you have"

    #Create embedding for the user query
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_ad_token_provider=token_provider,
            )
    embedded_query_results = aoai_embed_query(query=user_message, client=client)
    # print("Embedded Query Results:", len(embedded_query_results))

    # Define the query parameters
    results = mongo.retrieve_documents(embedded_query=embedded_query_results,
            search_index_name=os.getenv("PRODUCT_SEARCH_INDEX"),
            search_column=os.getenv("SEARCH_COLUMN"),
            collection_name=os.getenv("MONGODB_COLLECTION"),
            db_name=os.getenv("MONGODB_DATABASE"),
        )

    # return results
    # return print (mongo.list_collections(db_name=os.getenv("MONGODB_DATABASE")))
    # results = mongo.list_search_indexes(collection_name=os.getenv("MONGODB_COLLECTION"), db_name=os.getenv("MONGODB_DATABASE"))
    return results


if __name__ == "__main__":
    results = main()
    for result in results:
        print(result)
    # main()