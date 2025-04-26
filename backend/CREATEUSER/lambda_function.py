import boto3
import os
import json
import hmac
import hashlib
import base64
import uuid
from datetime import datetime

# Initialize AWS services
cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')

# Environment variables
USER_POOL_ID = os.environ['USER_POOL_ID']
TABLE_NAME = os.environ['USER_TABLE']
COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
COGNITO_CLIENT_SECRET = os.environ['COGNITO_CLIENT_SECRET']

def calculate_secret_hash(username):
    """Calculate the SECRET_HASH required for Cognito API calls."""
    message = username + COGNITO_CLIENT_ID
    secret = bytes(COGNITO_CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def check_email_exists(email):
    """Check if a user with the given email already exists in Cognito."""
    try:
        response = cognito.list_users(
            UserPoolId=USER_POOL_ID,
            Filter=f'email = "{email}"'
        )
        return len(response['Users']) > 0
    except Exception as e:
        print(f"Error checking email: {str(e)}")
        return False

def get_user_attributes(username):
    """Retrieve user attributes from Cognito."""
    try:
        response = cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
        return attributes
    except Exception as e:
        print(f"Error fetching user attributes: {str(e)}")
        return None

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        action = body.get('action', 'signup')

        if action == 'signup':
            # Extract fields from request
            email = body['email']
            password = body['password']
            first_name = body['firstName']
            last_name = body['lastName']
            phone = body.get('phone', '')
            user_role = body['userRole']

            # Check if email already exists
            if check_email_exists(email):
                return {
                    "statusCode": 400,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                    },
                    "body": json.dumps({"success": False, "message": "Email already exists!"})
                }

            # Generate unique username
            username = f"{first_name.lower()}.{last_name.lower()}{uuid.uuid4().hex[:6]}"
            secret_hash = calculate_secret_hash(username)

            # Sign up the user in Cognito
            cognito.sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                Password=password,
                SecretHash=secret_hash,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'given_name', 'Value': first_name},
                    {'Name': 'family_name', 'Value': last_name},
                    {'Name': 'phone_number', 'Value': phone},
                    {'Name': 'custom:userRole', 'Value': user_role}
                ]
            )

            return {
                "statusCode": 201,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({"success": True, "message": "Sign-up successful! Check your email for verification.", "username": username})
            }

        elif action == 'confirm':
            # Confirm user account using the verification code
            username = body['username']
            verification_code = body['verificationCode']
            user_role = body['userRole']  # Ensure role is passed

            cognito.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                ConfirmationCode=verification_code,
                SecretHash=calculate_secret_hash(username)
            )

            # Fetch user details from Cognito
            user_attributes = get_user_attributes(username)
            if not user_attributes:
                return {
                    "statusCode": 500,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                    },
                    "body": json.dumps({"success": False, "message": "Failed to fetch user details."})
                }

            # Extract details
            email = user_attributes.get('email')
            first_name = user_attributes.get('given_name')
            last_name = user_attributes.get('family_name')
            phone = user_attributes.get('phone_number')

            # Add user to Cognito group
            cognito.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=username,
                GroupName=user_role
            )
#
            # Store user details in DynamoDB
            table = dynamodb.Table(TABLE_NAME)
            user_id = str(uuid.uuid4())  # Generate new UUID
            now = datetime.utcnow().isoformat()

            table.put_item(
                Item={
                    'userId': user_id,
                    'username': username,
                    'email': email,
                    'firstName': first_name,
                    'lastName': last_name,
                    'phone': phone,
                    'role': user_role,
                    'createdAt': now,
                    'updatedAt': now
                }
            )

            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({"success": True, "message": "Account verified successfully!", "redirect": "/login"})
            }

        elif action == 'resend_verification':
            # Resend the verification code
            username = body['username']

            cognito.resend_confirmation_code(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                SecretHash=calculate_secret_hash(username)
            )

            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({"success": True, "message": "Verification code resent successfully."})
            }

        else:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({"success": False, "message": f"Invalid action: {action}"})
            }

    except cognito.exceptions.CodeMismatchException:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"success": False, "message": "Invalid verification code."})
        }

    except cognito.exceptions.ExpiredCodeException:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"success": False, "message": "Verification code expired."})
        }

    except cognito.exceptions.UserNotFoundException:
        return {
            "statusCode": 404,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"success": False, "message": "User not found. Please sign up first."})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"success": False, "message": f"An error occurred: {str(e)}"})
        }
