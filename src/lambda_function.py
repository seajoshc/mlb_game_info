#!/usr/bin/env
"""
AWS Lambda function that grabs MLB Gameday data and formats
it for consumption by Alexa Skills Kit Flash Briefing
v1.0.0
github.com/irlrobot
"""
from __future__ import print_function
import os
import time
import datetime
import json
import boto3
from botocore.exceptions import ClientError
import mlbgame

def lambda_handler(dummy_event, dummy_context):
    '''
    main function for aws lambda
    '''
    print('=========lambda_handler started...')
    day = time.strftime("%-d")
    month = time.strftime("%-m")
    year = time.strftime("%Y")
    games = mlbgame.day(int(year), int(month), int(day), home="Rays", away="Rays")
    title_text = "Tampa Bay Rays Game Info"

    if len(games) > 0:
        main_text = "The Tampa Bay Rays play the Boston Red Sox today at 1:05pm Eastern."
    else:
        main_text = "There are no games scheduled today."

    write_to_s3(generate_json(title_text, main_text), "tampa_bay_rays")

def generate_json(title_text, main_text):
    '''
    generate the flash briefing json
    '''
    utc_datetime = datetime.datetime.utcnow()
    timestamp = utc_datetime.strftime("%Y-%M-%dT%H:%m:%S.0Z")
    data = {
        "uid": "0",
        "updateDate": timestamp,
        "titleText": title_text,
        "mainText": main_text,
        "redirectionUrl": "https://www.mlb.tv"
    }
    return json.dumps(data)

def write_to_s3(json_content, team_name):
    '''
    write to s3 bucket
    '''
    print('=========json_content:  ' + json_content)
    print('=========team_name:  ' + team_name)
    bucket_key = os.environ['S3_BUCKET_KEY'] + '/' + team_name + '.json'
    print('=========trying to write: ' + bucket_key)
    try:
        client = boto3.client('s3')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False
    try:
        client.put_object(
            Body=json_content,
            Bucket=os.environ['S3_BUCKET'],
            Key=bucket_key
        )
    except ClientError as err:
        print("Failed to upload artifact to S3.\n" + str(err))
        return False

    print('=========s3 write successful')
    return True
