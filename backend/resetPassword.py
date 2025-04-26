import boto3
import os
import json
import hmac
import hashlib
import base64

# Initialize AWS Cognito client
cognito = boto3.client('cognito-idp')

# Environment variables
COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')  # Optional, if using client secret
USER_POOL_ID = os.environ['USER_POOL_ID']  # Required for admin_get_user

def calculate_secret_hash(username):
    """
    Calculate the SECRET_HASH required for Cognito API calls when client secret is enabled.
    """
    if not COGNITO_CLIENT_SECRET:
        return None  # If no client secret, skip SECRET_HASH
    message = username + COGNITO_CLIENT_ID
    secret = bytes(COGNITO_CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def check_user_exists(email):
    """
    Check if a user exists in Cognito using admin_get_user.
    """
    try:
        cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=email
        )
        return True
    except cognito.exceptions.UserNotFoundException:
        return False

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        email = body['email']
        action = body.get('action', 'initiate')  # Default action is 'initiate'

        print(f"Processing {action} request for email: {email}")

        # Check if user exists in Cognito
        if not check_user_exists(email):
            print(f"User not found: {email}")
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({"success": False, "message": f"User not found: {email}"})
            }

        # Calculate SECRET_HASH if client secret is enabled
        secret_hash = calculate_secret_hash(email)

        if action == 'initiate':
            # Step 1: Initiate password reset (send verification code)
            cognito.forgot_password(
                ClientId=COGNITO_CLIENT_ID,
                Username=email,
                SecretHash=secret_hash  # Include SECRET_HASH here if applicable
            )
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({"success": True, "message": "Password reset initiated. Please check your email."})
            }

        elif action == 'confirm':
            # Step 2: Confirm password reset (set new password)
            verification_code = body['verificationCode']
            new_password = body['newPassword']

            cognito.confirm_forgot_password(
                ClientId=COGNITO_CLIENT_ID,
                Username=email,
                ConfirmationCode=verification_code,
                Password=new_password,
                SecretHash=secret_hash  # Include SECRET_HASH here if applicable
            )
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({"success": True, "message": "Password reset successful."})
            }

        else:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({"success": False, "message": f"Invalid action: {action}"})
            }

    except cognito.exceptions.CodeMismatchException as e:
        print(f"Invalid verification code for email: {email}. Error: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({"success": False, "message": f"Invalid verification code: {str(e)}"})
        }

    except cognito.exceptions.InvalidParameterException as e:
        print(f"Invalid parameter for email: {email}. Error: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "message": "Invalid parameters provided."
            })
        }

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "message": "An internal error occurred. Please try again later."
            })
        }
