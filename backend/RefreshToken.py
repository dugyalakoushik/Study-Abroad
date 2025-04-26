import json
import boto3
import os
import hmac
import hashlib
import base64

# Initialize Cognito client
cognito = boto3.client('cognito-idp')

# Environment variables for Cognito configuration
USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')

# Ensure required environment variables are set
if not all([USER_POOL_ID, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("Missing required environment variables")

# Helper function to calculate secret hash for Cognito authentication
def calculate_secret_hash(username):
    message = username + CLIENT_ID
    secret = bytes(CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

# Helper function to get user info from Cognito
def get_cognito_username(email):
    try:
        user_info = cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=email
        )
        return user_info['Username']
    except Exception as e:
        print(f"User not found or error fetching user: {str(e)}")
        return email

# Helper function to respond with HTTP response
def create_response(status_code, message, data=None):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }
    body = {"success": status_code == 200, "message": message}
    if data:
        body.update(data)

    return {
        "statusCode": status_code,
        "headers": cors_headers,
        "body": json.dumps(body)
    }

# Handle token refresh
def handle_token_refresh(email, refresh_token):
    if not refresh_token:
        return create_response(400, "Refresh token is required")

    try:
        username = get_cognito_username(email)
        secret_hash = calculate_secret_hash(username)
        print(f"Calculated secret hash for {username}")

        # Attempt refresh token flow with secret hash
        response = cognito.initiate_auth(
            AuthFlow='REFRESH_TOKEN_AUTH',
            ClientId=CLIENT_ID,
            AuthParameters={
                'USERNAME': username,
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': secret_hash
            }
        )
        tokens = response.get('AuthenticationResult', {})

        return create_response(
            200, 
            "Token refresh successful",
            {
                "idToken": tokens.get('IdToken'),
                "accessToken": tokens.get('AccessToken'),
                "expiresIn": tokens.get('ExpiresIn')
            }
        )
    except Exception as e:
        print(f"Token refresh failed: {str(e)}")
        return create_response(401, "Token refresh failed. Please login again.", {"error": str(e)})

# Lambda handler function
def lambda_handler(event, context):
    try:
        print(f"Event received: {event}")
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        action = body.get('action')
        refresh_token = body.get('refreshToken')

        if not email:
            return create_response(400, "Email is required")

        if action == 'refresh':
            return handle_token_refresh(email, refresh_token)
        else:
            return create_response(400, "Invalid action")

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return create_response(500, "Internal server error", {"error": str(e)})
