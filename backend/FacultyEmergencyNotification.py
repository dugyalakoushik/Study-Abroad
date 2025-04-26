import json
import boto3
import os

# Initialize AWS services
'''dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')'''


dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

def normalize_name(name):
    """Standardize faculty name formatting for consistent SNS filtering"""
    if not name:
        return ""
    # Remove any special characters, keep only alphanumeric and spaces
    clean_name = ''.join(c for c in name if c.isalnum() or c == ' ')
    # Replace spaces with hyphens
    return clean_name.replace(' ', '-')

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))

    try:
        # Process DynamoDB Stream records
        for record in event['Records']:
            if record['eventName'] == 'INSERT' or record['eventName'] == 'MODIFY':
                new_image = record['dynamodb']['NewImage']

                # Check if the emergency column is set to true
                if new_image.get('emergency', {}).get('BOOL', False):
                    # Extract user name and other details
                    user_name = new_image.get('name', {}).get('S')
                    latitude = new_image.get('latitude', {}).get('N')
                    longitude = new_image.get('longitude', {}).get('N')
                    address = new_image.get('address', {}).get('S')
                    emergency_details = new_image.get('emergencyDetails', {}).get('S', 'No details provided')

                    print(f"Processing emergency for user: {user_name}, at location: {latitude}, {longitude}")

                    # Retrieve Classes Trips table name from environment variable
                    classes_trips_table_name = os.environ.get('CLASSES_TRIPS_TABLE', 'ClassesTrips')
                    classes_trips_table = dynamodb.Table(classes_trips_table_name)

                    # Scan for class/trip containing the user in studentsList
                    scan_kwargs = {
                        'FilterExpression': 'contains(studentsList, :user)',
                        'ExpressionAttributeValues': {':user': user_name}
                    }

                    print(f"Scanning {classes_trips_table_name} for student: {user_name}")
                    classes_response = classes_trips_table.scan(**scan_kwargs)

                    if 'Items' not in classes_response or len(classes_response['Items']) == 0:
                        print(f"No class/trip found for student: {user_name}")
                        continue  # Skip to next record

                    print(f"Found {len(classes_response['Items'])} class(es)/trip(s) for student: {user_name}")

                    # Iterate through each class/trip found for this student
                    for class_trip in classes_response['Items']:
                        faculty_list = class_trip.get('facultyList', [])
                        class_id = class_trip.get('classId')
                        # Revert back to className to see if it sends
                        class_name = class_trip.get('name', 'Unknown Class')

                        print(f"Processing class: {class_name} (ID: {class_id})")

                        # Handle both array and string formats for faculty list
                        if isinstance(faculty_list, str):
                            faculty_list = [f.strip() for f in faculty_list.split(',')]
                        
                        print(f"Faculty list: {faculty_list}")

                        if not faculty_list:
                            print(f"No faculty members found for classId: {class_id}")
                            continue

                        # Construct the message for the emergency alert
                        message_body = {
                            "alert": {
                                "student": user_name,
                                "className": class_name,
                                "classId": class_id,
                                "location": {
                                    "address": address,
                                    "latitude": latitude,
                                    "longitude": longitude
                                },
                                "emergencyDetails": emergency_details
                            },
                            "targetFaculty": faculty_list  # This will be used for message filtering
                        }
                        
                        # Format the message for human reading
                        human_readable_message = f"""
                        🚨 Emergency Alert 🚨

                        Student: {user_name}
                        Class: {class_name}
                        Location: {address}
                        Coordinates: {latitude}, {longitude}
                        Emergency Details: {emergency_details}

                        Please take immediate action!
                        """

                        # Publish the message to the SNS topic with message attributes for filtering
                        faculty_topic_arn = os.environ.get('FACULTY_TOPIC_ARN')
                        if not faculty_topic_arn:
                            print("ERROR: Missing FACULTY_TOPIC_ARN environment variable")
                            continue
                            
                        print(f"Using SNS Topic ARN: {faculty_topic_arn}")
                        
                        # Create message attributes for filtering
                        message_attributes = {}
                        
                        # Create a single attribute that applies to all recipients
                        # This ensures message gets published even if specific faculty filters fail
                        message_attributes["all-faculty"] = {
                            'DataType': 'String',
                            'StringValue': 'true'
                        }
                        
                        # Add individual faculty filters
                        for faculty in faculty_list:
                            try:
                                normalized_faculty = normalize_name(faculty)
                                if normalized_faculty:
                                    attr_key = f"faculty-{normalized_faculty}"
                                    print(f"Adding message attribute: {attr_key}")
                                    message_attributes[attr_key] = {
                                        'DataType': 'String',
                                        'StringValue': 'true'
                                    }
                            except Exception as e:
                                print(f"Error processing faculty name '{faculty}': {str(e)}")
                        
                        try:
                            # ADDED LOGGING HERE
                            print(f"About to publish to SNS. class_name: {class_name}, user_name: {user_name}")
                            response = sns.publish(
                                TopicArn=faculty_topic_arn,
                                Message=json.dumps({
                                    "default": json.dumps(message_body),
                                    "email": human_readable_message
                                }),
                                Subject=f"Emergency Alert - {user_name} in {class_name}",
                                MessageStructure='json',
                                MessageAttributes=message_attributes
                            )
                            print(f"SNS publish successful. MessageId: {response.get('MessageId')}")
                        except Exception as sns_error:
                            print(f"Error sending SNS message: {str(sns_error)}")
                            # Continue processing other classes even if this one fails...
            else:
                print(f"Record event was not INSERT or MODIFY: {record['eventName']}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Successfully processed emergency alerts'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error processing emergency alerts: {str(e)}'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }


