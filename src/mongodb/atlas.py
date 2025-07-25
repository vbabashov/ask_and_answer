import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi



def get_mongo_client() -> MongoClient:
    """
    Get Mongo Client

    :return: Mongodb Client
    """
    client = MongoClient(
        server_api=ServerApi('1'),
        host=os.getenv('MONGODB_URI'),
        tls=True,
        authMechanism='MONGODB-X509',
        authSource='$external',
        tlsCertificateKeyFile=os.path.join(os.getcwd(), os.getenv("MONGODB_CERT_PATH")), # os.getenv('MONGODB_CERT_PATH')
        tlsAllowInvalidCertificates=False,
        directConnection=False,
        tlsAllowInvalidHostnames=True,
    )
    try:
        client.admin.command('ping')
        print('Pinged your deployment. You successfully connected to MongoDB!')
    except Exception as e:
        raise (e)

    return client
