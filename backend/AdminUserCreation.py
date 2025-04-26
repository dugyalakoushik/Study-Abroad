import boto3
import os
import json
import uuid
from datetime import datetime
import hmac
import hashlib
import base64

# Initialize AWS services
cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Environment variables
USER_POOL_ID = os.environ['USER_POOL_ID']
TABLE_NAME = os.environ['USER_TABLE']
COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
COGNITO_CLIENT_SECRET = os.environ['COGNITO_CLIENT_SECRET']
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
STUDENT_SNS_TOPIC_ARN = os.environ.get('STUDENT_SNS_TOPIC_ARN')

def normalize_name(name):
    """Standardize faculty name formatting for consistent SNS filtering"""
    if not name:
        return ""
    # Remove any special characters, keep only alphanumeric and spaces
    clean_name = ''.join(c for c in name if c.isalnum() or c == ' ')
    # Replace spaces with hyphens
    return clean_name.replace(' ', '-')

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

def subscribe_faculty_to_sns(email, full_name=""):
    """Subscribe faculty to SNS topic - filter policy will be set later when we have the name"""
    try:
        if not SNS_TOPIC_ARN:
            print("SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
            return False

        print(f"Subscribing faculty {email} to SNS topic: {SNS_TOPIC_ARN}")
        
        response = sns.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )
        
        subscription_arn = response['SubscriptionArn']
        print(f"Subscription ARN: {subscription_arn}")
        
        # If we have a name and the subscription is confirmed, set filter policy
        if full_name and subscription_arn != 'pending confirmation':
            normalized_name = normalize_name(full_name)
            filter_policy = {
                f"faculty-{normalized_name}": ["true"],
                "all-faculty": ["true"]
            }
            
            sns.set_subscription_attributes(
                SubscriptionArn=subscription_arn,
                AttributeName='FilterPolicy',
                AttributeValue=json.dumps(filter_policy)
            )
            print(f"Filter policy set for {email}")
        
        return True
    except Exception as e:
        print(f"Error subscribing {email} to SNS: {str(e)}")
        return False

def subscribe_student_to_sns(email):
    """Subscribe student to the student SNS topic."""
    try:
        if not STUDENT_SNS_TOPIC_ARN:
            print("STUDENT_SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
            return False

        print(f"Subscribing student {email} to SNS topic: {STUDENT_SNS_TOPIC_ARN}")
        
        response = sns.subscribe(
            TopicArn=STUDENT_SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email
        )
        
        print(f"Subscription initiated for {email}")
        return True
    except Exception as e:
        print(f"Error subscribing {email} to SNS: {str(e)}")
        return False

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        # Parse request body
        body = json.loads(event['body'])
        action = body.get('action', 'create_user')

        if action == 'create_user':
            # Extract minimal required user details
            email = body['email']
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
            
            # Generate username from email
            email_prefix = email.split('@')[0]
            username = f"{email_prefix}-{uuid.uuid4().hex[:8]}"
            
            # Create the user in Cognito with minimal attributes
            cognito.admin_create_user(
                UserPoolId=USER_POOL_ID,
                Username=username,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},  # Pre-verify the email
                    {'Name': 'custom:userRole', 'Value': user_role}
                ],
                MessageAction='SUPPRESS'  # Don't send welcome email since they'll use Google
            )
            
            # Add user to appropriate Cognito group
            cognito.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=username,
                GroupName=user_role
            )
            
            # Create a minimal DynamoDB entry that will be updated on first login
            table = dynamodb.Table(TABLE_NAME)
            user_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            table.put_item(
                Item={
                    'userId': user_id,
                    'username': username,
                    'email': email,
                    'firstName': "",  # Will be filled in from Google profile
                    'lastName': "",   # Will be filled in from Google profile
                    'name': "",       # Will be filled in from Google profile
                    'phone': "",      # Will be filled in from Google profile if available
                    'role': user_role,
                    'createdAt': now,
                    'updatedAt': now
                }
            )
            
            # Subscribe to SNS based on role
            if user_role == 'faculty' and SNS_TOPIC_ARN:
                subscribe_faculty_to_sns(email)
            elif user_role == 'student' and STUDENT_SNS_TOPIC_ARN:
                subscribe_student_to_sns(email)
            
            return {
                "statusCode": 201,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({
                    "success": True,
                    "message": f"User created successfully. An invitation has been sent to {email} to sign in with Google.",
                    "username": username,
                    "userId": user_id
                })
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
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps({"success": False, "message": f"An error occurred: {str(e)}"})
        }
