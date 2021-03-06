from __future__ import print_function

import os
import json
import urllib
import boto3
import time
import datetime
import sys

s3 = boto3.resource('s3')
rekognition = boto3.client('rekognition')

def lambda_handler(event, context):
    jst = datetime.datetime.now()
    now = jst.strftime("%Y-%m-%d %H:%M:%S")
    bucket_name = 'mitsu-face-check'

    images_bucket = event['Records'][0]['s3']['bucket']['name']
    images_key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    result_folder = 'result/' + images_key.rsplit('/', 1)[1].rsplit('.', 1)[0]
    results_bucket = s3.Bucket(bucket_name)

##############
    label_record = [0]*5
    label_record[0] = (images_key)
    label_record[1] = (now)

    reko_response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': images_bucket,
                    'Name': images_key,
                },
            },
            MaxLabels=20
        )

    for label in reko_response['Labels'] :
        if label["Name"] == "Human" or label["Name"] == "People" or label["Name"] == "Person":
            label_record[2] = (1)

##############
    reko_response_face = rekognition.detect_faces(
        Image={
            'S3Object': {
                'Bucket': images_bucket,
                'Name': images_key,
            },
        },
        Attributes=[
            'ALL',
            ]
    )

    for label in reko_response_face['FaceDetails'] :
        if label["Smile"]['Value'] == True:
            smile_value =  1*label["Smile"]['Confidence']
            label_record[3] = (smile_value)
        if label["Smile"]['Value'] == False:
            smile_value = -1*label["Smile"]['Confidence']
            label_record[3] = (smile_value)

        if label["EyesOpen"]['Value'] == True:
            eye_value =  1*label["EyesOpen"]['Confidence']
            label_record[4] = (eye_value)
        if label["EyesOpen"]['Value'] == False:
            eye_value = -1*label["EyesOpen"]['Confidence']
            label_record[4] = (eye_value)

    label_records = ','.join(map(str, label_record)) + '\n'
    s3_response = results_bucket.put_object( \
        ACL='private', \
        Body=label_records, \
        Key=result_folder + ".csv", \
        ContentType='text/plain' \
    )

    boto3.client('s3').delete_object(Bucket=bucket_name, Key=images_key)
    return str(s3_response)
