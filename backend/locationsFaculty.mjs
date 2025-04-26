import { DynamoDBClient, ScanCommand } from '@aws-sdk/client-dynamodb';

const dynamodbClient = new DynamoDBClient({ region: 'us-east-1' });

export const handler = async (event) => {
    try {
        // Get faculty name from various possible sources
        let facultyName;
        
        // Check if it's in query parameters
        if (event.queryStringParameters && event.queryStringParameters.facultyName) {
            facultyName = event.queryStringParameters.facultyName;
        } 
        // Check if it's in the POST body
        else if (event.body) {
            try {
                const body = JSON.parse(event.body);
                facultyName = body.facultyName;
            } catch (e) {
                console.error("Error parsing request body:", e);
            }
        }

        if (!facultyName) {
            return {
                statusCode: 400,
                headers: { 'Access-Control-Allow-Origin': '*' },
                body: JSON.stringify({ message: 'Faculty name is required' })
            };
        }

        // Step 1: Get classes/trips taught by this faculty
        const classParams = {
            TableName: 'ClassesTrips',
            FilterExpression: "contains(facultyList, :faculty)",
            ExpressionAttributeValues: { ":faculty": { S: facultyName } }
        };

        const classesData = await dynamodbClient.send(new ScanCommand(classParams));

        // Step 2: Extract student names from these classes
        const studentSet = new Set();
        classesData.Items.forEach(classItem => {
            if (classItem.studentsList && Array.isArray(classItem.studentsList.L)) {
                classItem.studentsList.L.forEach(student => {
                    studentSet.add(student.S);
                });
            }
        });

        // Step 3: Get all location data with additional fields
        const locationParams = {
            TableName: 'Locations',
            ProjectionExpression: "#nm, address, #dt, latitude, longitude, mapsLink, #tm, emergency, emergencyDetails, peers, place, studentStatus, comments",
            ExpressionAttributeNames: { 
                "#nm": "name",
                "#dt": "date",
                "#tm": "time"
            }
        };

        const locationsData = await dynamodbClient.send(new ScanCommand(locationParams));

        // Step 4: Filter locations to include only students in faculty's classes
        const latestEntries = locationsData.Items.reduce((acc, item) => {
            const name = item.name.S;

            // Skip if not in faculty's class
            if (!studentSet.has(name)) return acc;

            const entryTime = new Date(`${item.date.S}T${item.time.S}`).getTime();

            // Keep only the latest entry for each student
            if (!acc[name] || entryTime > acc[name].timestamp) {
                acc[name] = {
                    name: item.name.S,
                    address: item.address.S,
                    date: item.date.S,
                    time: item.time.S,
                    latitude: parseFloat(item.latitude.N),
                    longitude: parseFloat(item.longitude.N),
                    mapsLink: item.mapsLink.S,
                    emergency: item.emergency?.BOOL || false,
                    emergencyDetails: item.emergencyDetails?.S || '',
                    peers: item.peers?.S || 'None',
                    place: item.place?.S || '',
                    studentStatus: item.studentStatus?.S || 'None',
                    comments: item.comments?.S || '',
                    timestamp: entryTime
                };
            }
            return acc;
        }, {});

        return {
            statusCode: 200,
            headers: { 
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' 
            },
            body: JSON.stringify(Object.values(latestEntries))
        };
    } catch (error) {
        console.error('Error fetching locations:', error);
        return {
            statusCode: 500,
            headers: { 'Access-Control-Allow-Origin': '*' },
            body: JSON.stringify({ message: 'Failed to fetch locations' })
        };
    }
};
