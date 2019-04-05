import uuid
from elasticsearch import Elasticsearch
from utility import logger
# from handler.db_handler import get_result_from_db

ES_HOST = "search-od-happy-face-5i3vty7clvmiz3cvgus3n6dfpa.us-east-1.es.amazonaws.com"
ES_INDEX_NAME = "test"

def get_es():
    es = None
    try:
        es = Elasticsearch([{"host": ES_HOST, "port": 80}])
    except Exception as e:
        raise Exception('Error while creating Elasticsearch client', e)
    if not es:
        raise Exception('Error while creating Elasticsearch client', e)
    return es


def push_data_to_es(img_uuid, img_list):
    logger.info("Adding data to index..")
    best_path = img_list[0]['path']
    for img in img_list:
        item_uuid = str(uuid.uuid4())
        logger.info(img["date"].split(".")[0])
        es_dict = dict(path=img['path'],
                       confidence=img['emotions']['Confidence'],
                       best_path=best_path,
                       date=img['date'],
                       image_uuid=img_uuid)
        res = get_es().index(index=ES_INDEX_NAME, doc_type='result', id=item_uuid, body=es_dict)
        logger.info(res['result'])


# def push_data_to_final_result_es():
#     doc = get_result_from_db()
#     for d in doc['Items']:
#         logger.info("Adding result data to index..", type(d))
#         item_uuid = str(uuid.uuid4())
#         es_dict = dict(s3_path=d['path'], confidence=d['confidence'])
#         res = get_es().index(index=ES_INDEX_NAME, doc_type='final_result', id=item_uuid, body=es_dict)
#         logger.info(res['result'])


def create_indices():
    INDEX_NAME = "test"
    es = Elasticsearch([{"host": "search-od-happy-face-5i3vty7clvmiz3cvgus3n6dfpa.us-east-1.es.amazonaws.com",
                         "port": 80}])

    if es.indices.exists(INDEX_NAME):
        logger.info("deleting '%s' index..." % (INDEX_NAME))
        res = es.indices.delete(index=INDEX_NAME)
        logger.info(" response: '%s'" % (res))

    request_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        'mappings': {
            'result': {
                'properties': {
                    "date": {
                        "type": "date",
                        "format": "YYYY-MM-DD H:mm:ss",
                        "store": True
                    },

                    'image_uuid': {
                        "type": "text",
                        "fields": {
                            "raw": {
                                "type": "keyword"
                            }
                        }
                    },
                    'path': {
                        "type": "text",
                        "fields": {
                            "rawPath": {
                                "type": "keyword"
                            }
                        }
                    },
                    'best_path': {
                        "type": "text",
                        "fields": {
                            "rawBestPath": {
                                "type": "keyword"
                            }
                        }
                    },
                    'confidence': {'type': 'float'},
                }
            }
        }
    }

    logger.info("creating '%s' index..." % (INDEX_NAME))
    res = es.indices.create(index=INDEX_NAME, body=request_body)
    logger.info(res)

# create_indices()