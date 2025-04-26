#Trying code in progress
'''
import json
import boto3
import os

# Initialize AWS services
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')

# Fetching the environment variables
CLASSES_TRIPS_TABLE = os.environ.get('CLASSES_TRIPS_TABLE', 'ClassesTrips')
STUDENT_SNS_TOPIC_ARN = os.environ.get('STUDENT_SNS_TOPIC_ARN')
USERS_TABLE = os.environ.get('USERS_TABLE', 'Users')

def normalize_name(name):
    """Standardize name formatting for consistent SNS filtering"""
    if not name:
        return ""
    # Remove any special characters, keep only alphanumeric and spaces
    clean_name = ''.join(c for c in name if c.isalnum() or c == ' ')
    # Replace spaces with hyphens
    return clean_name.replace(' ', '-')

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        # 1. Parse request body
        try:
            body = json.loads(event['body'])
        except (json.JSONDecodeError, KeyError) as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Invalid request body'}),
                'headers': headers
            }

        # 2. Extract required fields
        faculty_name = body.get('facultyName')
        message_title = body.get('title', 'Notification from Study Abroad Program')
        message_content = body.get('message', 'Please check your study abroad program portal for important updates.')
        specific_class_id = body.get('classId')  # Optional: to send to students of specific class only
        
        if not faculty_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'facultyName field is required'}),
                'headers': headers
            }

        # 3. Get classes for this faculty member
        classes_trips_table = dynamodb.Table(CLASSES_TRIPS_TABLE)
        
        if specific_class_id:
            # Get specific class
            try:
                class_response = classes_trips_table.get_item(
                    Key={'classId': specific_class_id}
                )
                classes_items = [class_response.get('Item')] if 'Item' in class_response else []
                
                # Verify faculty is part of this class
                if classes_items and classes_items[0].get('facultyList') and faculty_name not in classes_items[0].get('facultyList', []):
                    return {
                        'statusCode': 403,
                        'body': json.dumps({'message': 'Faculty is not authorized for this class'}),
                        'headers': headers
                    }
            except Exception as e:
                print(f"Error retrieving specific class: {str(e)}")
                classes_items = []
        else:
            # Get all classes for this faculty
            scan_kwargs = {
                'FilterExpression': 'contains(facultyList, :faculty)',
                'ExpressionAttributeValues': {':faculty': faculty_name}
            }
            classes_response = classes_trips_table.scan(**scan_kwargs)
            classes_items = classes_response.get('Items', [])
        
        if not classes_items:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No classes found for this faculty'}),
                'headers': headers
            }

        # 4. Collect student names from the classes
        students_list = []
        class_details = {}
        
        for class_item in classes_items:
            class_id = class_item.get('classId')
            class_name = class_item.get('name', 'Unnamed Class')
            
            # Store class details for later use
            class_details[class_id] = {
                'name': class_name,
                'students': []
            }
            
            # Get students from this class
            if 'studentsList' in class_item:
                for student_entry in class_item['studentsList']:
                    # Extract student name based on the format (using 'S' key if it's a DynamoDB object)
                    if isinstance(student_entry, dict) and 'S' in student_entry:
                        student_name = student_entry['S']
                    else:
                        student_name = student_entry
                    
                    if student_name and student_name not in students_list:
                        students_list.append(student_name)
                        class_details[class_id]['students'].append(student_name)

        if not students_list:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No students found in these classes'}),
                'headers': headers
            }

        # 5. Send notifications to students
        success_count = 0
        failure_count = 0
        notification_results = []
        
        for student_name in students_list:
            try:
                # Format the message
                formatted_message = {
                    'title': message_title,
                    'message': message_content,
                    'facultyName': faculty_name,
                    'timestamp': str(context.invoked_function_arn).split(':')[5]  # Use request ID as timestamp
                }
                
                # Classes this student belongs to
                student_classes = []
                for class_id, details in class_details.items():
                    if student_name in details['students']:
                        student_classes.append({
                            'classId': class_id,
                            'className': details['name']
                        })
                        formatted_message['classes'] = student_classes
                
                # Normalize student name for SNS filter
                normalized_student_name = normalize_name(student_name)
                
                # Create message attributes for targeting this specific student
                message_attributes = {
                    f"student-{normalized_student_name}": {
                        "DataType": "String",
                        "StringValue": "true"
                    },
                    "all-students": {
                        "DataType": "String",
                        "StringValue": "true"
                    }
                }
                
                # Send the notification
                response = sns.publish(
                    TopicArn=STUDENT_SNS_TOPIC_ARN,
                    Message=json.dumps(formatted_message),
                    Subject=message_title,
                    MessageAttributes=message_attributes
                )
                
                print(f"Sent notification to student {student_name}, MessageId: {response['MessageId']}")
                success_count += 1
                notification_results.append({
                    'student': student_name,
                    'status': 'success',
                    'messageId': response['MessageId']
                })
                
            except Exception as e:
                print(f"Failed to send notification to student {student_name}: {str(e)}")
                failure_count += 1
                notification_results.append({
                    'student': student_name,
                    'status': 'failure',
                    'error': str(e)
                })

        # 6. Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully notified {success_count} students. Failed to notify {failure_count} students.',
                'success': success_count,
                'failure': failure_count,
                'results': notification_results,
                'classes': [{'classId': c_id, 'name': details['name']} for c_id, details in class_details.items()]
            }),
            'headers': headers
        }

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error processing request: {str(e)}'}),
            'headers': headers
        }
'''

import json
import boto3
import os
from datetime import datetime

# Initialize AWS services
'''dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')'''

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Fetching the environment variables
CLASSES_TRIPS_TABLE = os.environ.get('CLASSES_TRIPS_TABLE', 'ClassesTrips')
STUDENT_SNS_TOPIC_ARN = os.environ.get('STUDENT_SNS_TOPIC_ARN')
USERS_TABLE = os.environ.get('USERS_TABLE', 'Users')

def normalize_name(name):
    """Standardize name formatting for consistent SNS filtering"""
    if not name:
        return ""
    # Remove any special characters, keep only alphanumeric and spaces
    clean_name = ''.join(c for c in name if c.isalnum() or c == ' ')
    # Replace spaces with hyphens
    return clean_name.replace(' ', '-')

def format_email_message(student_name, faculty_name, message_title, message_content, student_classes, custom_status_options=None):
    """
    Format a more personalized and meaningful email message
    """
    now = datetime.now()
    formatted_date = now.strftime("%B %d, %Y")
    
    # Create a list of classes the student is part of
    class_list = ""
    for idx, class_info in enumerate(student_classes):
        class_list += f"{idx+1}. {class_info['className']}\n"
    
    # Format status options if provided
    status_options = ""
    if custom_status_options and isinstance(custom_status_options, list) and len(custom_status_options) > 0:
        status_options = "Available status options:\n"
        for idx, status in enumerate(custom_status_options):
            if isinstance(status, dict) and 'S' in status:
                status_options += f"- {status['S']}\n"
            else:
                status_options += f"- {status}\n"
    
    # Construct the email message
    email_message = f"""
Dear {student_name},

{message_content}

This notification relates to the following program(s):
{class_list}

{status_options}

Please log into the Study Abroad Portal to update your status and ensure your safety information is current.

Sent by: {faculty_name}
Date: {formatted_date}

TEXAS A&M UNIVERSITY
Study Abroad Programs
+1 (979) 123-4567
http://studyabroad.tamu.edu

IMPORTANT: This email contains information related to your participation in a Texas A&M University study abroad program. Please do not ignore this communication.
"""
    return email_message

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        # 1. Parse request body
        try:
            body = json.loads(event['body'])
        except (json.JSONDecodeError, KeyError) as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Invalid request body'}),
                'headers': headers
            }

        # 2. Extract required fields
        faculty_name = body.get('facultyName')
        message_title = body.get('title', 'Important: Study Abroad Program Update')
        message_content = body.get('message', 'Please update your location status for your study abroad program.')
        specific_class_id = body.get('classId')  # Optional: to send to students of specific class only
        
        if not faculty_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'facultyName field is required'}),
                'headers': headers
            }

        # 3. Get classes for this faculty member
        classes_trips_table = dynamodb.Table(CLASSES_TRIPS_TABLE)
        
        if specific_class_id:
            # Get specific class
            try:
                class_response = classes_trips_table.get_item(
                    Key={'classId': specific_class_id}
                )
                classes_items = [class_response.get('Item')] if 'Item' in class_response else []
                
                # Verify faculty is part of this class
                if classes_items and faculty_name not in classes_items[0].get('facultyList', []):
                    return {
                        'statusCode': 403,
                        'body': json.dumps({'message': 'Faculty is not authorized for this class'}),
                        'headers': headers
                    }
            except Exception as e:
                print(f"Error retrieving specific class: {str(e)}")
                classes_items = []
        else:
            # Get all classes for this faculty
            scan_kwargs = {
                'FilterExpression': 'contains(facultyList, :faculty)',
                'ExpressionAttributeValues': {':faculty': faculty_name}
            }
            classes_response = classes_trips_table.scan(**scan_kwargs)
            classes_items = classes_response.get('Items', [])
        
        if not classes_items:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No classes found for this faculty'}),
                'headers': headers
            }

        # 4. Collect student names from the classes
        students_list = []
        class_details = {}
        
        for class_item in classes_items:
            class_id = class_item.get('classId')
            class_name = class_item.get('name', 'Unnamed Class')
            custom_status = class_item.get('customstatus', [])
            
            # Store class details for later use
            class_details[class_id] = {
                'name': class_name,
                'students': [],
                'customStatus': custom_status
            }
            
            # Get students from this class
            if 'studentsList' in class_item:
                for student_entry in class_item['studentsList']:
                    # Extract student name based on the format (using 'S' key if it's a DynamoDB object)
                    if isinstance(student_entry, dict) and 'S' in student_entry:
                        student_name = student_entry['S']
                    else:
                        student_name = student_entry
                    
                    if student_name and student_name not in students_list:
                        students_list.append(student_name)
                        class_details[class_id]['students'].append(student_name)

        if not students_list:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No students found in these classes'}),
                'headers': headers
            }

        # 5. Send notifications to students
        success_count = 0
        failure_count = 0
        notification_results = []
        
        for student_name in students_list:
            try:
                # Gather all classes this student belongs to
                student_classes = []
                custom_status_options = []
                
                for class_id, details in class_details.items():
                    if student_name in details['students']:
                        student_classes.append({
                            'classId': class_id,
                            'className': details['name']
                        })
                        # Get custom status options if available
                        if details['customStatus'] and len(details['customStatus']) > 0:
                            for status in details['customStatus']:
                                if status not in custom_status_options:
                                    custom_status_options.append(status)
                
                # Format a meaningful email message
                email_message = format_email_message(
                    student_name=student_name,
                    faculty_name=faculty_name,
                    message_title=message_title,
                    message_content=message_content,
                    student_classes=student_classes,
                    custom_status_options=custom_status_options
                )
                
                # JSON payload for the mobile app
                json_payload = {
                    'title': message_title,
                    'message': message_content,
                    'facultyName': faculty_name,
                    'timestamp': datetime.now().isoformat(),
                    'classes': student_classes,
                    'statusOptions': custom_status_options
                }
                
                # Normalize student name for SNS filter
                normalized_student_name = normalize_name(student_name)
                
                # Create message attributes for targeting this specific student
                message_attributes = {
                    f"student-{normalized_student_name}": {
                        "DataType": "String",
                        "StringValue": "true"
                    },
                    "all-students": {
                        "DataType": "String",
                        "StringValue": "true"
                    }
                }
                
                # Send the notification - format differently for email vs. mobile
                response = sns.publish(
                    TopicArn=STUDENT_SNS_TOPIC_ARN,
                    Message=json.dumps({
                        'default': json.dumps(json_payload),
                        'email': email_message,
                        'sms': f"{message_title}: {message_content[:100]}..." if len(message_content) > 100 else f"{message_title}: {message_content}"
                    }),
                    Subject=message_title,
                    MessageStructure='json',
                    MessageAttributes=message_attributes
                )
                
                print(f"Sent notification to student {student_name}, MessageId: {response['MessageId']}")
                success_count += 1
                notification_results.append({
                    'student': student_name,
                    'status': 'success',
                    'messageId': response['MessageId']
                })
                
            except Exception as e:
                print(f"Failed to send notification to student {student_name}: {str(e)}")
                failure_count += 1
                notification_results.append({
                    'student': student_name,
                    'status': 'failure',
                    'error': str(e)
                })

        # 6. Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully notified {success_count} students. Failed to notify {failure_count} students.',
                'success': success_count,
                'failure': failure_count,
                'results': notification_results,
                'classes': [{'classId': c_id, 'name': details['name']} for c_id, details in class_details.items()]
            }),
            'headers': headers
        }

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error processing request: {str(e)}'}),
            'headers': headers
        }
