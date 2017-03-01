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
import uuid
import boto3
from botocore.exceptions import ClientError
import mlbgame

def lambda_handler(dummy_event, dummy_context):
    '''
    main function for aws lambda
    '''
    print('=========lambda_handler started...')
    time.tzset()
    print('=========container timezone is:  ' + str(time.tzname))
    for team in mlbgame.teams():
        get_team_info(team.club_common_name, team.club_full_name)

def get_team_info(team_short_name, team_full_name):
    '''
    get all info for a team
    '''
    print('=========Working on:  ' + team_full_name)
    # get today's games
    games_today = mlbgame.day(
        int(time.strftime("%Y")), int(time.strftime("%-m")),
        int(time.strftime("%-d")), home=team_short_name, away=team_short_name
    )
    # get yesterday's games
    yesterday = datetime.date.fromordinal(datetime.date.today().toordinal()-1)
    games_yesterday = mlbgame.day(
        int(yesterday.strftime("%Y")), int(yesterday.strftime("%-m")),
        int(yesterday.strftime("%-d")), home=team_short_name, away=team_short_name
    )
    title_text = team_full_name + " Game Info"

    if len(games_today) > 0:
        today_text = get_todays_game_information(games_today, team_short_name)
    else:
        today_text = "There are no games scheduled today for the " + \
            team_short_name + "."

    if len(games_yesterday) > 0:
        yesterday_text = get_yesterdays_game_information(games_yesterday, team_short_name)
    else:
        yesterday_text = "The " + team_short_name + " did not play yesterday."

    main_text = yesterday_text + " " + today_text
    write_to_s3(generate_json(title_text, main_text), team_short_name)

def generate_json(title_text, main_text):
    '''
    generate the flash briefing json
    '''
    uid = uuid.uuid1()
    utc_datetime = datetime.datetime.utcnow()
    timestamp = utc_datetime.strftime("%Y-%m-%dT%H:%M:%S.0Z")
    data = {
        "uid": uid.urn,
        "updateDate": timestamp,
        "titleText": title_text,
        "mainText": main_text
    }
    return json.dumps(data, indent=2)

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
            ContentType="application/json",
            Body=json_content,
            Bucket=os.environ['S3_BUCKET'],
            Key=bucket_key
        )
    except ClientError as err:
        print("Failed to upload artifact to S3.\n" + str(err))
        return False

    print('=========s3 write successful')
    return True

def get_todays_game_information(games_today, team):
    '''
    parse info for today's games
    '''
    if games_today[0].game_status == 'FINAL':
        try:
            status = get_win_status(team, games_today[0].w_team)
        except AttributeError as dummy_err:
            status = "tied"
        return "Today, the " + team + " " + status + ". The score was " + \
            games_today[0].nice_score() + ". "
    else:
        return "Today, the " + games_today[0].away_team + " will play the " + \
            games_today[0].home_team + " at " + games_today[0].game_start_time + \
            " Eastern time."

def get_yesterdays_game_information(games_yesterday, team):
    '''
    parse info for yesterday's games
    '''
    try:
        status = get_win_status(team, games_yesterday[0].w_team)
    except AttributeError as dummy_err:
        status = "tied"

    return "Yesterday, the " + team + " " + status + ". The score was " + \
        games_yesterday[0].nice_score() + ". "

def get_win_status(team, winning_team):
    '''
    determine if the team won, lost, or tied
    '''
    if winning_team == team:
        return "won"
    else:
        return "lost"
