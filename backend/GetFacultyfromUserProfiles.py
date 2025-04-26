'''import json
import boto3
import os
from boto3.dynamodb.conditions import Attr

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Ensure the environment variable is set
USER_TABLE_NAME = os.environ.get('USERS_TABLE')
if not USER_TABLE_NAME:
    raise ValueError("Environment variable USERS_TABLE is not set")

user_table = dynamodb.Table(USER_TABLE_NAME)

def lambda_handler(event, context):
    try:
        students = []
        last_evaluated_key = None

        # Paginate through all items
        while True:
            scan_kwargs = {
                "FilterExpression": Attr('role').eq('faculty')
            }
            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = user_table.scan(**scan_kwargs)
            students.extend(response.get('Items', []))

            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break  # No more pages

        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
            },
            'body': json.dumps(students, default=str)
        }

    except Exception as e:
        print(f"Error fetching students: {str(e)}")  # Logs for debugging
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
            },
            'body': json.dumps({'error': 'Failed to fetch faculty'})
        }'''


import json
import boto3
import os
from boto3.dynamodb.conditions import Attr

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Ensure the environment variables are set
USER_TABLE_NAME = os.environ.get('USERS_TABLE')
TRIP_TABLE_NAME = os.environ.get('TRIP_TABLE')

if not USER_TABLE_NAME or not TRIP_TABLE_NAME:
    raise ValueError("Environment variables USERS_TABLE or TRIP_TABLE are not set")

user_table = dynamodb.Table(USER_TABLE_NAME)
trip_table = dynamodb.Table(TRIP_TABLE_NAME)

def lambda_handler(event, context):
    try:
        faculty = []
        last_evaluated_key = None
        existing_faculty_in_trips = set()

        # Fetch all faculty already part of a trip (using pagination)
        while True:
            trip_response = trip_table.scan()
            for trip in trip_response.get('Items', []):
                # Collect all faculty in each trip's facultyList
                for faculty_member in trip.get('facultyList', []):
                    # Check if the faculty member is a dictionary and extract the name correctly
                    if isinstance(faculty_member, dict):
                        # Assuming the faculty member is stored as a dictionary with a key 'S'
                        faculty_name = faculty_member.get('S')
                    else:
                        # If it's a simple string, assume it's the faculty's name
                        faculty_name = faculty_member
                    
                    if faculty_name:
                        existing_faculty_in_trips.add(faculty_name)
        
            last_evaluated_key = trip_response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break  # No more pages of trips

        # Paginate through all users and filter out faculty already part of a trip
        while True:
            scan_kwargs = {
                "FilterExpression": Attr('role').eq('faculty')
            }
            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = user_table.scan(**scan_kwargs)
            for faculty_member in response.get('Items', []):
                faculty_name = faculty_member.get('name')  # Assuming 'name' is the faculty name field
                if faculty_name not in existing_faculty_in_trips:
                    faculty.append(faculty_member)

            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break  # No more pages of users

        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
            },
            'body': json.dumps(faculty, default=str)
        }

    except Exception as e:
        print(f"Error fetching faculty: {str(e)}")  # Logs for debugging
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
            },
            'body': json.dumps({'error': 'Failed to fetch faculty members not in any trip'})
        }
