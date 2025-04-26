import boto3
import os
import json
import hmac
import hashlib
import base64

cognito = boto3.client('cognito-idp')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')

if not all([USER_POOL_ID, CLIENT_ID, CLIENT_SECRET]):
    raise ValueError("Missing required environment variables")

def calculate_secret_hash(username):
    message = username + CLIENT_ID
    secret = bytes(CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def check_user_exists(email):
    try:
        cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
        return True
    except cognito.exceptions.UserNotFoundException:
        return False

def get_user_role(email):
    try:
        user_info = cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
        role = next((attr['Value'] for attr in user_info['UserAttributes'] if attr['Name'] == 'custom:userRole'), None)
        print(f"Retrieved role for {email}: {role}")
        return role
    except Exception as e:
        print(f"Error fetching role for {email}: {str(e)}")
        return None

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body['email']
        action = body.get('action', 'login')
        
        print(f"Processing {action} request for email: {email}")
        user_exists = check_user_exists(email)
        
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        }
        
        if action == 'check':
            return {
                "statusCode": 200 if user_exists else 404,
                "headers": cors_headers,
                "body": json.dumps({
                    "success": user_exists,
                    "message": "User exists" if user_exists else "User not found"
                })
            }
            
        elif action == 'login':
            if not user_exists:
                return {"statusCode": 404, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Login failed: User not found"})}
            if 'password' not in body:
                return {"statusCode": 400, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Login failed: Password is required"})}
            
            secret_hash = calculate_secret_hash(email)
            auth_response = cognito.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                ClientId=CLIENT_ID,
                AuthParameters={'USERNAME': email, 'PASSWORD': body['password'], 'SECRET_HASH': secret_hash}
            )
            tokens = auth_response.get('AuthenticationResult', {})
            role = get_user_role(email)
            
            print(f"Login successful for email: {email}, role: {role}")
            
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "success": True,
                    "message": f"Login successful for {email}",
                    "idToken": tokens.get('IdToken'),
                    "accessToken": tokens.get('AccessToken'),
                    "refreshToken": tokens.get('RefreshToken') if body.get('remember', False) else None,
                    "role": role,
                    "expiresIn": tokens.get('ExpiresIn')  # Include expiry time
                })
            }
    except cognito.exceptions.NotAuthorizedException as e:
        return {"statusCode": 401, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: Incorrect password for {email}"})}
    except cognito.exceptions.UserNotConfirmedException:
        return {"statusCode": 403, "headers": cors_headers, "body": json.dumps({"success": False, "message": f"Login failed: User not confirmed: {email}"})}
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {"statusCode": 500, "headers": cors_headers, "body": json.dumps({"success": False, "message": "Internal server error"})}
    