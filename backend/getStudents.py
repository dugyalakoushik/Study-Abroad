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
                "FilterExpression": Attr('role').eq('student')
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
            'body': json.dumps({'error': 'Failed to fetch students'})
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
        students = []
        last_evaluated_key = None
        existing_students_in_trips = set()

        # Fetch all students already part of a trip (using pagination)
        while True:
            trip_response = trip_table.scan()
            for trip in trip_response.get('Items', []):
                # Collect all students in each trip's studentsList
                for student in trip.get('studentsList', []):
                    # Check if the student is a dictionary and extract the name correctly
                    if isinstance(student, dict):
                        # Assuming the student is stored as a dictionary with a key 'S'
                        student_name = student.get('S')
                    else:
                        # If it's a simple string, assume it's the student's name
                        student_name = student
                    
                    if student_name:
                        existing_students_in_trips.add(student_name)
        
            last_evaluated_key = trip_response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break  # No more pages of trips

        # Paginate through all users and filter out students already part of a trip
        while True:
            scan_kwargs = {
                "FilterExpression": Attr('role').eq('student')
            }
            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = user_table.scan(**scan_kwargs)
            for student in response.get('Items', []):
                student_name = student.get('name')  # Assuming 'name' is the student name field
                if student_name not in existing_students_in_trips:
                    students.append(student)

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
            'body': json.dumps({'error': 'Failed to fetch students'})
        }
