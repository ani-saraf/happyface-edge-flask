import ast
import json
import os
import tempfile
import uuid
from time import gmtime, strftime

import boto3
from PIL import Image

from utility import logger
from handler.db_handler import get_face_group_data, save_face_group_data
from handler.es_handler import push_data_to_es

ES_HOST = "search-od-happy-face-5i3vty7clvmiz3cvgus3n6dfpa.us-east-1.es.amazonaws.com"
ES_INDEX_NAME = "test"
GROUP_PHOTOS = "group_snaps"
REGION_NAME = 'us-east-1'
DYNAMO_TBL_FACEGROUPS = 'FaceGroupsEdge'

rek_client = boto3.client('rekognition', region_name=REGION_NAME)
s3_client = boto3.client('s3', region_name=REGION_NAME)
s3 = boto3.resource('s3', region_name=REGION_NAME)
dynamo_client = boto3.client('dynamodb', region_name=REGION_NAME)
dynamodb = boto3.resource('dynamodb', REGION_NAME)

s3_bucket = 'image-recognition-edge'
bucket = s3.Bucket(s3_bucket)

tmp = "{}/happyface".format(tempfile.gettempdir())
x, y = 2592, 1944
similarity_q = 50.00


def process_image(tmp_path):
    logger.info("\nStarted processing photo {}".format(tmp_path))
    try:
        with open(tmp_path, "rb") as imageFile:
            f = imageFile.read()
            b = bytearray(f)
    except Exception as e:
        logger.error('Error occurred while opening image file: {}'.format(str(e)))
        raise Exception('Error occurred while opening image file: ', e)

    try:
        group_s3_path = "{}/{}".format(GROUP_PHOTOS, os.path.basename(tmp_path))
        logger.info("Uploading photo : " + group_s3_path)
        s3_client.upload_file(tmp_path, s3_bucket, group_s3_path, ExtraArgs={'ACL': 'public-read'})
        s3.ObjectAcl(s3_bucket, group_s3_path).put(ACL='public-read')
        logger.info("Photo uploaded")
        response = rek_client.detect_faces(
            Image={
                'Bytes': b
            },
            Attributes=[
                'ALL',
            ]
        )
        for index, image in enumerate(response['FaceDetails']):
            path = os.path.join(tmp, os.path.basename(tmp_path).rstrip("/"))
            img = Image.open(path)
            width, height, left, top = image['BoundingBox']['Width'], \
                                       image['BoundingBox']['Height'], \
                                       image['BoundingBox']['Left'], \
                                       image['BoundingBox']['Top']
            left, top, right, bottom = left * x, top * y, (left + width) * x, (height + top) * y
            cropped = img.crop((left, top, right, bottom))
            cropped = cropped.resize((100, 100), Image.ANTIALIAS)

            dir_path = os.path.join(tmp, os.path.basename(tmp_path).split(".")[0])



            if not os.path.exists(dir_path):
                os.mkdir(dir_path)
            thum_uuid = str(uuid.uuid4())
            thumbnail_path = os.path.join(dir_path, thum_uuid + ".jpeg")
            cropped.save(thumbnail_path)
            s3_thumbnail_path = "thumbnail/{}".format(
                os.path.basename(tmp_path).split(".")[0] + "_" + os.path.basename(thumbnail_path))



            happy_emotion = {'Type': 'HAPPY', 'Confidence': 0.0}
            for emotion in image['Emotions']:
                # if emotion['Type'] == 'HAPPY' and emotion['Confidence'] > 90:
                if emotion['Type'] == 'HAPPY':
                    happy_emotion = emotion

                    # upload thumbnail to s3
                    logger.info("Uploading thumbnail: " + s3_thumbnail_path)
                    s3_client.upload_file(thumbnail_path, s3_bucket, s3_thumbnail_path, ExtraArgs={'ACL': 'public-read'})
                    s3.ObjectAcl(s3_bucket, s3_thumbnail_path).put(ACL='public-read')
                    os.remove(thumbnail_path)
                    os.rmdir(dir_path)

                    # Compare with existing thumnails and store data in FaceGroups
                    compare_existing_thumbnails(s3_thumbnail_path, happy_emotion)

        logger.info("Completed processing photo {}\n".format(tmp_path))

    except Exception as e:
        logger.error('Error occurred while detecting faces: {}'.format(str(e)))
        raise Exception('Error occurred while detecting faces:', e)


def compare_existing_thumbnails(thumbnail_path, emotions):
    s3_thumbnail_path = os.path.join("https://s3.amazonaws.com", s3_bucket, thumbnail_path)
    face_group_result = get_face_group_data()
    now = str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    if face_group_result['Items']:
        is_face_matched = False
        for i in face_group_result['Items']:
            json_str = json.dumps(i)
            resp_dict = json.loads(json_str)
            target_image_list = ast.literal_eval(resp_dict['image_list'])
            target_path = "thumbnail" + target_image_list[0]['path'].split("thumbnail")[1]
            if target_path != thumbnail_path:
                img_uuid = resp_dict['uuid']
                compare_response = compare_faces(thumbnail_path, target_path)
                if compare_response is not None:
                    if compare_response['FaceMatches']:
                        for dictionary in compare_response['FaceMatches']:
                            if float(dictionary['Similarity']) > similarity_q:
                                t_dict = dict(path=s3_thumbnail_path, emotions=emotions, date=now)
                                target_image_list.append(t_dict)
                                save_face_group_data(img_uuid, target_image_list)
                                push_data_to_es(img_uuid, [t_dict])
                                is_face_matched = True
                                break

        if not is_face_matched:
            img_uuid = str(uuid.uuid4())
            image_list = [dict(path=s3_thumbnail_path, emotions=emotions, date=now)]
            save_face_group_data(img_uuid, image_list)
            push_data_to_es(img_uuid, image_list)
    else:
        img_uuid = str(uuid.uuid4())
        image_list = [dict(path=s3_thumbnail_path, emotions=emotions, date=now)]
        save_face_group_data(img_uuid, image_list)
        push_data_to_es(img_uuid, image_list)


def compare_faces(src_image, target_image):
    # logger.info("src_image: ", src_image, "target_image: ", target_image)
    try:
        response = rek_client.compare_faces(
            SourceImage={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': src_image
                }
            },
            TargetImage={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': target_image
                }
            }
        )
        return response
    except Exception as e:
        logger.error('\nError occurred while comparing faces using rekognition : {}'.format(str(e)))
        logger.error('Error comparing images ({}) and ({}) '.format(src_image, target_image))
        # raise Exception('Error occurred while comparing faces using rekognition: ', e)
        pass


# process_image("C:/Users/anisaraf/Desktop/test/Image_20190306_121818.jpg")
