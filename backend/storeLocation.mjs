/*import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

const dynamodbClient = new DynamoDBClient({ region: 'us-east-1' });
const sesClient = new SESClient({ region: 'us-east-1' });

export const handler = async (event) => {
    try {
        const { 
            id, 
            latitude, 
            longitude, 
            address, 
            name, 
            peers = 'None', 
            place = '', 
            comments = '',
            emergency = false,
            emergencyDetails = ''
        } = typeof event === 'string' ? JSON.parse(event) : event;

        // Validate required fields
        if (!id || !latitude || !longitude || !address || !name) {
            return {
                statusCode: 400,
                headers: { "Access-Control-Allow-Origin": "*" },
                body: JSON.stringify({ message: 'Missing required attributes' }),
            };
        }

        // Generate timestamp
        const now = new Date();
        const timestamp = Math.floor(now.getTime() / 1000);
        const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;

        // Store in DynamoDB
        const params = {
            TableName: 'Locations',
            Item: {
                id: { S: id },
                latitude: { N: String(latitude) },
                longitude: { N: String(longitude) },
                address: { S: address },
                timestamp: { N: String(timestamp) },
                date: { S: date },
                time: { S: time },
                mapsLink: { S: `https://www.google.com/maps?q=${latitude},${longitude}` },
                name: { S: name },
                peers: { S: peers },
                place: { S: place },
                comments: { S: comments },
                emergency: { BOOL: emergency },
                emergencyDetails: { S: emergencyDetails }
            }
        };

        await dynamodbClient.send(new PutItemCommand(params));

        // Send email for emergenciees

        return {
            statusCode: 200,
            headers: { "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({
                message: emergency ? 'Emergency signal received' : 'Location stored',
                id,
                name,
                latitude,
                longitude,
                address,
                mapsLink
            }),
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            headers: { "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({ message: 'Server error' }),
        };
    }
};*/

/*import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

const dynamodbClient = new DynamoDBClient({ region: 'us-east-1' });
const sesClient = new SESClient({ region: 'us-east-1' });

export const handler = async (event) => {
    try {
        const { 
            id, 
            latitude, 
            longitude, 
            address, 
            name, 
            peers = 'None', 
            place = '', 
            comments = '',
            emergency = false,
            emergencyDetails = ''
        } = typeof event === 'string' ? JSON.parse(event) : event;

        // Validate required fields
        if (!id || !latitude || !longitude || !address || !name) {
            return {
                statusCode: 400,
                headers: { "Access-Control-Allow-Origin": "*" },
                body: JSON.stringify({ message: 'Missing required attributes' }),
            };
        }

        // Generate timestamp
        const now = new Date();
        const timestamp = Math.floor(now.getTime() / 1000);
        const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;

        // Build the base item
        const item = {
            id: { S: id },
            latitude: { N: String(latitude) },
            longitude: { N: String(longitude) },
            address: { S: address },
            timestamp: { N: String(timestamp) },
            date: { S: date },
            time: { S: time },
            mapsLink: { S: `https://www.google.com/maps?q=${latitude},${longitude}` },
            name: { S: name },
            place: { S: place },
            comments: { S: comments },
            emergency: { BOOL: emergency },
            emergencyDetails: { S: emergencyDetails }
        };

        // Only include peers if it's NOT an emergency
        if (!emergency) {
            item.peers = { S: peers };
        }

        const params = {
            TableName: 'Locations',
            Item: item
        };

        await dynamodbClient.send(new PutItemCommand(params));

        return {
            statusCode: 200,
            headers: { "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({
                message: emergency ? 'Emergency signal received' : 'Location stored',
                id,
                name,
                latitude,
                longitude,
                address,
                mapsLink: item.mapsLink.S
            }),
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            headers: { "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({ message: 'Server error' }),
        };
    }
};
*/


import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

const dynamodbClient = new DynamoDBClient({ region: 'us-east-1' });
const sesClient = new SESClient({ region: 'us-east-1' });

export const handler = async (event) => {
    try {
        const {
            id,
            latitude,
            longitude,
            address,
            name,
            peers = 'None',
            place = '',
            comments = '',
            emergency = false,
            emergencyDetails = '',
            studentStatus = 'None' // ADDED studentStatus
        } = typeof event === 'string' ? JSON.parse(event) : event;

        // Validate required fields
        if (!id || !latitude || !longitude || !address || !name) {
            return {
                statusCode: 400,
                headers: { "Access-Control-Allow-Origin": "*" },
                body: JSON.stringify({ message: 'Missing required attributes' }),
            };
        }

        // Generate timestamp
        const now = new Date();
        const timestamp = Math.floor(now.getTime() / 1000);
        const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;

        // Build the base item
        const item = {
            id: { S: id },
            latitude: { N: String(latitude) },
            longitude: { N: String(longitude) },
            address: { S: address },
            timestamp: { N: String(timestamp) },
            date: { S: date },
            time: { S: time },
            mapsLink: { S: `https://www.google.com/maps?q=${latitude},${longitude}` },
            name: { S: name },
            place: { S: place },
            comments: { S: comments },
            emergency: { BOOL: emergency },
            emergencyDetails: { S: emergencyDetails },
            studentStatus: { S: studentStatus }  //ADDED studentStatus
        };

        // Only include peers if it's NOT an emergency
        if (!emergency) {
            item.peers = { S: peers };
        }

        const params = {
            TableName: 'Locations',
            Item: item
        };

        await dynamodbClient.send(new PutItemCommand(params));

        return {
            statusCode: 200,
            headers: { "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({
                message: emergency ? 'Emergency signal received' : 'Location stored',
                id,
                name,
                latitude,
                longitude,
                address,
                mapsLink: item.mapsLink.S,
                studentStatus: item.studentStatus.S // ADDED studentStatus
            }),
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            headers: { "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({ message: 'Server error' }),
        };
    }
};
