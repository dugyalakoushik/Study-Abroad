'''import boto3
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
sns = boto3.client('sns')

# Environment variables
USER_POOL_ID = os.environ['USER_POOL_ID']
TABLE_NAME = os.environ['USER_TABLE']
COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
COGNITO_CLIENT_SECRET = os.environ['COGNITO_CLIENT_SECRET']
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
STUDENT_SNS_TOPIC_ARN = os.environ.get('STUDENT_SNS_TOPIC_ARN')  # Ensure this is set

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

def subscribe_faculty_to_email_sns(email, full_name):
    """
    Subscribe the faculty member's email to the SNS topic
    and add a filter policy matching their name.
    """
    try:
        if not SNS_TOPIC_ARN:
            print("SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
            return False

        print(f"Subscribing faculty {full_name} ({email}) to SNS topic: {SNS_TOPIC_ARN}")

        # Create a standardized version of the name for filtering
        normalized_name = normalize_name(full_name)

        # First create the subscription
        response = sns.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )

        subscription_arn = response['SubscriptionArn']
        print(f"Subscription ARN: {subscription_arn}")

        # If the subscription is pending confirmation, we can't set filter policy yet
        if subscription_arn == 'pending confirmation':
            print(f"Subscription for {email} is pending confirmation. Filter policy will need to be set after confirmation.")
            return True

        # Create filter policies that match both individual faculty name and all-faculty attributes
        filter_policy = {
            f"faculty-{normalized_name}": ["true"],
            "all-faculty": ["true"]
        }

        print(f"Setting filter policy for subscription: {json.dumps(filter_policy)}")

        sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName='FilterPolicy',
            AttributeValue=json.dumps(filter_policy)
        )

        print(f"Subscription and filter policy set for {email} with filter on faculty-{normalized_name}")
        return True
    except Exception as e:
        print(f"Error subscribing {email} to SNS: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def subscribe_student_to_email_sns(email, class_ids=None):
    """
    Subscribe the student's email to the student SNS topic.
    Optionally add filter policies for specific classes.
    """
    try:
        if not STUDENT_SNS_TOPIC_ARN:
            print("STUDENT_SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
            return False

        print(f"Subscribing student {email} to SNS topic: {STUDENT_SNS_TOPIC_ARN}")

        response = sns.subscribe(
            TopicArn=STUDENT_SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )

        subscription_arn = response['SubscriptionArn']
        print(f"Subscription ARN: {subscription_arn}")

        # If the subscription is pending confirmation, we can't set filter policy yet
        if subscription_arn == 'pending confirmation':
            print(f"Subscription for {email} is pending confirmation. Filter policy will need to be set after confirmation.")
            return True

        # Create filter policies for class-specific notifications
        filter_policy = {
            "all-students": ["true"]
        }
        
        # Add class-specific filters if provided
        if class_ids and isinstance(class_ids, list):
            for class_id in class_ids:
                normalized_class_id = normalize_id(class_id)
                filter_policy[f"class-{normalized_class_id}"] = ["true"]

        print(f"Setting filter policy for subscription: {json.dumps(filter_policy)}")

        sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName='FilterPolicy',
            AttributeValue=json.dumps(filter_policy)
        )

        print(f"Subscription and filter policy set for {email}")
        return True
    except Exception as e:
        print(f"Error subscribing {email} to SNS: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def update_sns_filter_policy(email, full_name):
    """Update SNS filter policy for faculty member after confirmation."""
    try:
        if not SNS_TOPIC_ARN:
            return False

        normalized_name = normalize_name(full_name)
        print(f"Looking for subscription for {email} to update filter policy")

        # Get a list of subscriptions for this topic
        response = sns.list_subscriptions_by_topic(TopicArn=SNS_TOPIC_ARN)

        # Find the subscription matching this email
        for subscription in response.get('Subscriptions', []):
            if subscription.get('Endpoint') == email:
                print(f"Found subscription: {subscription['SubscriptionArn']}")

                # Create filter policies that match both individual faculty name and all-faculty attributes
                filter_policy = {
                    f"faculty-{normalized_name}": ["true"],
                    "all-faculty": ["true"]
                }

                print(f"Setting filter policy: {json.dumps(filter_policy)}")

                sns.set_subscription_attributes(
                    SubscriptionArn=subscription['SubscriptionArn'],
                    AttributeName='FilterPolicy',
                    AttributeValue=json.dumps(filter_policy)
                )
                print(f"Filter policy updated for {email}")
                return True

        print(f"No subscription found for {email}")
        return False
    except Exception as e:
        print(f"Error updating filter policy for {email}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        # Parse request body
        body = json.loads(event['body'])
        action = body.get('action', 'signup')
        print(f"Processing action: {action}")

        if action == 'signup':
            # Extract fields from request
            email = body['email']
            password = body['password']

            # Handle different name formats - keep spaces in the stored name
            # but create username without spaces
            first_name = body.get('firstName', '').strip()
            last_name = body.get('lastName', '').strip()

            # If first_name contains multiple names (e.g., "Sai Koushik")
            # We'll still keep it as is for display purposes
            display_first_name = first_name
            display_last_name = last_name

            # Create a sanitized version for username creation
            # Remove any extra spaces and keep only alphanumeric chars
            clean_first = ''.join(e for e in first_name if e.isalnum() or e == ' ')
            clean_last = ''.join(e for e in last_name if e.isalnum() or e == ' ')

            # Create full name with proper spacing
            full_name = f"{display_first_name} {display_last_name}".strip()

            phone = body.get('phone', '')
            user_role = body['userRole']

            print(f"Processing signup for {full_name} ({email}) with role {user_role}")

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

            # Generate unique username - ensure no spaces
            username_base = clean_first.lower().replace(' ', '')
            if clean_last:
                username_base += '.' + clean_last.lower().replace(' ', '')
            username = f"{username_base}{uuid.uuid4().hex[:6]}"

            secret_hash = calculate_secret_hash(username)

            print(f"Generated username: {username}")

            # Sign up the user in Cognito
            cognito.sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                Password=password,
                SecretHash=secret_hash,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'given_name', 'Value': display_first_name},
                    {'Name': 'family_name', 'Value': display_last_name},
                    {'Name': 'phone_number', 'Value': phone},
                    {'Name': 'name', 'Value': full_name},  # Store full name with spaces
                    {'Name': 'custom:userRole', 'Value': user_role}
                ]
            )
            print(f"User successfully created in Cognito")

            # If the user is faculty, subscribe them to the SNS topic with filter policy
            if user_role == 'faculty': #Check to make sure it's a faculty first
                if not SNS_TOPIC_ARN: #And there is an ARN
                    print("SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
                else:
                    print(f"Attempting to subscribe faculty {full_name} to SNS")
                    if subscribe_faculty_to_email_sns(email, full_name):
                        print(f"Successfully subscribed faculty to SNS")
                    else:
                        print(f"Failed to subscribe faculty {email} to SNS topic.")

            # If the user is a student, subscribe them to the student SNS topic
            elif user_role == 'student':
                if not STUDENT_SNS_TOPIC_ARN: #Check to make sure that there is a student ARN
                    print("STUDENT_SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
                else:
                    print(f"Attempting to subscribe student {email} to SNS")
                    if subscribe_student_to_email_sns(email):
                        print(f"Successfully subscribed student to SNS")
                    else:
                        print(f"Failed to subscribe student {email} to student SNS topic.")

            return {
                "statusCode": 201,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({
                    "success": True,
                    "message": "Sign-up successful! Check your email for verification.",
                    "username": username,
                    "displayName": full_name  # Return the display name with spaces
                })
            }
        elif action == 'confirm':
            # Confirm user account using the verification code
            username = body['username']
            verification_code = body['verificationCode']
            user_role = body['userRole']  # Ensure role is passed

            print(f"Confirming user account for {username} with role {user_role}")

            cognito.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                ConfirmationCode=verification_code,
                SecretHash=calculate_secret_hash(username)
            )
            print(f"User account confirmed in Cognito")

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
            name = user_attributes.get('name')  # Get full name from Cognito

            print(f"Retrieved user attributes: {name}, {email}")

            # Add user to Cognito group
            cognito.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=username,
                GroupName=user_role
            )
            print(f"Added user to {user_role} group")

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
                    'name': name,  # Store full name with spaces in DynamoDB
                    'phone': phone,
                    'role': user_role,
                    'createdAt': now,
                    'updatedAt': now
                }
            )
            print(f"User details stored in DynamoDB")

            # For faculty, try to set the filter policy again in case the email was confirmed
            if user_role == 'faculty' and SNS_TOPIC_ARN and name and email:
                print(f"Updating SNS filter policy for confirmed faculty member")
                if update_sns_filter_policy(email, name):
                    print(f"Successfully updated SNS filter policy")
                else:
                    print(f"Failed to update SNS filter policy")

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
            print(f"Resending verification code for {username}")

            cognito.resend_confirmation_code(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                SecretHash=calculate_secret_hash(username)
            )
            print(f"Verification code resent")

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
'''



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
sns = boto3.client('sns')

# Environment variables
USER_POOL_ID = os.environ['USER_POOL_ID']
TABLE_NAME = os.environ['USER_TABLE']
COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
COGNITO_CLIENT_SECRET = os.environ['COGNITO_CLIENT_SECRET']
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
STUDENT_SNS_TOPIC_ARN = os.environ.get('STUDENT_SNS_TOPIC_ARN')  # Ensure this is set

def normalize_name(name):
    """Standardize name formatting for consistent SNS filtering"""
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

def subscribe_faculty_to_email_sns(email, full_name):
    """
    Subscribe the faculty member's email to the SNS topic
    and add a filter policy matching their name.
    """
    try:
        if not SNS_TOPIC_ARN:
            print("SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
            return False

        print(f"Subscribing faculty {full_name} ({email}) to SNS topic: {SNS_TOPIC_ARN}")

        # Create a standardized version of the name for filtering
        normalized_name = normalize_name(full_name)

        # First create the subscription
        response = sns.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )

        subscription_arn = response['SubscriptionArn']
        print(f"Subscription ARN: {subscription_arn}")

        # If the subscription is pending confirmation, we can't set filter policy yet
        if subscription_arn == 'pending confirmation':
            print(f"Subscription for {email} is pending confirmation. Filter policy will need to be set after confirmation.")
            return True

        # Create filter policies that match both individual faculty name and all-faculty attributes
        filter_policy = {
            f"faculty-{normalized_name}": ["true"],
            "all-faculty": ["true"]
        }

        print(f"Setting filter policy for subscription: {json.dumps(filter_policy)}")

        sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName='FilterPolicy',
            AttributeValue=json.dumps(filter_policy)
        )

        print(f"Subscription and filter policy set for {email} with filter on faculty-{normalized_name}")
        return True
    except Exception as e:
        print(f"Error subscribing {email} to SNS: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def subscribe_student_to_email_sns(email, full_name):
    """
    Subscribe the student's email to the student SNS topic
    and add a filter policy matching their name.
    """
    try:
        if not STUDENT_SNS_TOPIC_ARN:
            print("STUDENT_SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
            return False

        print(f"Subscribing student {full_name} ({email}) to SNS topic: {STUDENT_SNS_TOPIC_ARN}")

        # Create a standardized version of the name for filtering
        normalized_name = normalize_name(full_name)

        # First create the subscription
        response = sns.subscribe(
            TopicArn=STUDENT_SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )

        subscription_arn = response['SubscriptionArn']
        print(f"Subscription ARN: {subscription_arn}")

        # If the subscription is pending confirmation, we can't set filter policy yet
        if subscription_arn == 'pending confirmation':
            print(f"Subscription for {email} is pending confirmation. Filter policy will need to be set after confirmation.")
            return True

        # Create filter policies that match both individual student name and all-students attributes
        filter_policy = {
            f"student-{normalized_name}": ["true"],
            "all-students": ["true"]
        }

        print(f"Setting filter policy for subscription: {json.dumps(filter_policy)}")

        sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName='FilterPolicy',
            AttributeValue=json.dumps(filter_policy)
        )

        print(f"Subscription and filter policy set for {email} with filter on student-{normalized_name}")
        return True
    except Exception as e:
        print(f"Error subscribing {email} to SNS: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def update_sns_filter_policy(email, full_name, is_student=False):
    """Update SNS filter policy after confirmation."""
    try:
        # Select the appropriate topic ARN
        topic_arn = STUDENT_SNS_TOPIC_ARN if is_student else SNS_TOPIC_ARN
        
        if not topic_arn:
            return False

        normalized_name = normalize_name(full_name)
        print(f"Looking for subscription for {email} to update filter policy")

        # Get a list of subscriptions for this topic
        response = sns.list_subscriptions_by_topic(TopicArn=topic_arn)

        # Find the subscription matching this email
        for subscription in response.get('Subscriptions', []):
            if subscription.get('Endpoint') == email:
                print(f"Found subscription: {subscription['SubscriptionArn']}")

                # Create filter policies based on role
                if is_student:
                    filter_policy = {
                        f"student-{normalized_name}": ["true"],
                        "all-students": ["true"]
                    }
                else:
                    filter_policy = {
                        f"faculty-{normalized_name}": ["true"],
                        "all-faculty": ["true"]
                    }

                print(f"Setting filter policy: {json.dumps(filter_policy)}")

                sns.set_subscription_attributes(
                    SubscriptionArn=subscription['SubscriptionArn'],
                    AttributeName='FilterPolicy',
                    AttributeValue=json.dumps(filter_policy)
                )
                print(f"Filter policy updated for {email}")
                return True

        print(f"No subscription found for {email}")
        return False
    except Exception as e:
        print(f"Error updating filter policy for {email}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        # Parse request body
        body = json.loads(event['body'])
        action = body.get('action', 'signup')
        print(f"Processing action: {action}")

        if action == 'signup':
            # Extract fields from request
            email = body['email']
            password = body['password']

            # Handle different name formats - keep spaces in the stored name
            # but create username without spaces
            first_name = body.get('firstName', '').strip()
            last_name = body.get('lastName', '').strip()

            # If first_name contains multiple names (e.g., "Sai Koushik")
            # We'll still keep it as is for display purposes
            display_first_name = first_name
            display_last_name = last_name

            # Create a sanitized version for username creation
            # Remove any extra spaces and keep only alphanumeric chars
            clean_first = ''.join(e for e in first_name if e.isalnum() or e == ' ')
            clean_last = ''.join(e for e in last_name if e.isalnum() or e == ' ')

            # Create full name with proper spacing
            full_name = f"{display_first_name} {display_last_name}".strip()

            phone = body.get('phone', '')
            user_role = body['userRole']

            print(f"Processing signup for {full_name} ({email}) with role {user_role}")

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

            # Generate unique username - ensure no spaces
            username_base = clean_first.lower().replace(' ', '')
            if clean_last:
                username_base += '.' + clean_last.lower().replace(' ', '')
            username = f"{username_base}{uuid.uuid4().hex[:6]}"

            secret_hash = calculate_secret_hash(username)

            print(f"Generated username: {username}")

            # Sign up the user in Cognito
            cognito.sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                Password=password,
                SecretHash=secret_hash,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'given_name', 'Value': display_first_name},
                    {'Name': 'family_name', 'Value': display_last_name},
                    {'Name': 'phone_number', 'Value': phone},
                    {'Name': 'name', 'Value': full_name},  # Store full name with spaces
                    {'Name': 'custom:userRole', 'Value': user_role}
                ]
            )
            print(f"User successfully created in Cognito")

            # If the user is faculty, subscribe them to the SNS topic with filter policy
            if user_role == 'faculty': 
                if not SNS_TOPIC_ARN: 
                    print("SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
                else:
                    print(f"Attempting to subscribe faculty {full_name} to SNS")
                    if subscribe_faculty_to_email_sns(email, full_name):
                        print(f"Successfully subscribed faculty to SNS")
                    else:
                        print(f"Failed to subscribe faculty {email} to SNS topic.")

            # If the user is a student, subscribe them to the student SNS topic
            elif user_role == 'student':
                if not STUDENT_SNS_TOPIC_ARN: 
                    print("STUDENT_SNS_TOPIC_ARN environment variable not set. Skipping subscription.")
                else:
                    print(f"Attempting to subscribe student {full_name} to SNS")
                    if subscribe_student_to_email_sns(email, full_name):
                        print(f"Successfully subscribed student to SNS")
                    else:
                        print(f"Failed to subscribe student {email} to student SNS topic.")

            return {
                "statusCode": 201,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                "body": json.dumps({
                    "success": True,
                    "message": "Sign-up successful! Check your email for verification.",
                    "username": username,
                    "displayName": full_name  # Return the display name with spaces
                })
            }
        elif action == 'confirm':
            # Confirm user account using the verification code
            username = body['username']
            verification_code = body['verificationCode']
            user_role = body['userRole']  # Ensure role is passed

            print(f"Confirming user account for {username} with role {user_role}")

            cognito.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                ConfirmationCode=verification_code,
                SecretHash=calculate_secret_hash(username)
            )
            print(f"User account confirmed in Cognito")

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
            name = user_attributes.get('name')  # Get full name from Cognito

            print(f"Retrieved user attributes: {name}, {email}")

            # Add user to Cognito group
            cognito.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=username,
                GroupName=user_role
            )
            print(f"Added user to {user_role} group")

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
                    'name': name,  # Store full name with spaces in DynamoDB
                    'phone': phone,
                    'role': user_role,
                    'createdAt': now,
                    'updatedAt': now
                }
            )
            print(f"User details stored in DynamoDB")

            # Try to set the filter policy again in case the email was confirmed
            if name and email:
                is_student = user_role == 'student'
                topic_arn = STUDENT_SNS_TOPIC_ARN if is_student else SNS_TOPIC_ARN
                
                if topic_arn:
                    print(f"Updating SNS filter policy for confirmed {'student' if is_student else 'faculty'}")
                    if update_sns_filter_policy(email, name, is_student):
                        print(f"Successfully updated SNS filter policy")
                    else:
                        print(f"Failed to update SNS filter policy")

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
            print(f"Resending verification code for {username}")

            cognito.resend_confirmation_code(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                SecretHash=calculate_secret_hash(username)
            )
            print(f"Verification code resent")

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
