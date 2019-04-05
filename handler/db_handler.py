import ast
import json
import boto3
from utility import logger

REGION_NAME = 'us-east-1'
DYNAMO_TBL_FACEGROUPS = 'FaceGroupsEdge'
dynamo_client = boto3.client('dynamodb', region_name=REGION_NAME)
dynamodb = boto3.resource('dynamodb', REGION_NAME)

def get_face_group_data():
    try:
        table = dynamodb.Table(DYNAMO_TBL_FACEGROUPS)
        response = table.scan()
    except Exception as e:
        logger.error('Error occurred fetching face data from dynammodb: {}'.format(str(e)))
        raise Exception('Error occurred fetching face data from dynammodb:', e)

    return response



def save_face_group_data(img_uuid, image_list):
    try:
        response = dynamo_client.put_item(
            Item={
                'uuid': {
                    'S': img_uuid,
                },
                'image_list': {
                    'S': str(image_list),
                },
            },
            ReturnConsumedCapacity='TOTAL',
            TableName=DYNAMO_TBL_FACEGROUPS,
        )
    except Exception as e:
        logger.error('Error occurred while storing face data: {}'.format(str(e)))
        raise Exception('Error occurred while storing face data:', e)
    return response

def store_result_to_db(result_dict_list):
    for res_dict in result_dict_list:
        try:
            response = dynamo_client.put_item(
                Item={
                    'path': {
                        'S': res_dict['image'],
                    },
                    'confidence': {
                        'N': str(res_dict['confidence']),
                    },
                },
                ReturnConsumedCapacity='TOTAL',
                TableName='Results',
            )
        except Exception as e:
            logger.error('Error occurred while storing image {} result data : {}'.format(res_dict['image'], str(e)))
            raise Exception('Error occurred while storing image {} result data : {}'.format(res_dict['image'], str(e)))




# def get_result():
#     face_group_result = get_face_group_data()
#     result_dict_list = []
#     if face_group_result['Items']:
#         for i in face_group_result['Items']:
#             json_str = json.dumps(i)
#             resp_dict = json.loads(json_str)
#             target_image_list = ast.literal_eval(resp_dict['image_list'])
#             sum = 0
#             max_confidence = 0
#             happy_path = None
#             for image_dict in target_image_list:
#                 confidence = image_dict['emotions']['Confidence']
#                 if max_confidence < confidence:
#                     max_confidence = confidence
#                     happy_path = image_dict['path']
#                 sum += confidence
#             average_confidence = sum / len(target_image_list)
#             result_dict_list.append(dict(image=happy_path, confidence=average_confidence))
#
#     store_result_to_db(result_dict_list)
#     return result_dict_list


# def get_result_from_db():
#     try:
#         table = dynamodb.Table('Results')
#         response = table.scan()
#     except Exception as e:
#         logger.error('Error occurred fetching result data from dynammodb: {}'.format(str(e)))
#         raise Exception('Error occurred fetching result data from dynammodb:', e)
#
#     return response

def delete_items_from_db():
    table = dynamodb.Table(DYNAMO_TBL_FACEGROUPS)
    response = dynamo_client.describe_table(TableName=DYNAMO_TBL_FACEGROUPS)
    keys = [k['AttributeName'] for k in response['Table']['KeySchema']]
    response = table.scan()
    items = response['Items']
    number_of_items = len(items)
    if number_of_items == 0:  # no items to delete
        logger.info("Table '{}' is empty.".format(DYNAMO_TBL_FACEGROUPS))
        return
    logger.info("Deleting all ({}) items from table '{}'.".format(number_of_items, DYNAMO_TBL_FACEGROUPS))
    with table.batch_writer() as batch:
        for item in items:
            key_dict = {k: item[k] for k in keys}
            logger.info("Deleting " + str(item) + "...")
            batch.delete_item(Key=key_dict)


