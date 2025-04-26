// index.mjs
import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';

const dynamodbClient = new DynamoDBClient({ region: 'us-east-1' });

export const handler = async (event) => {
    try {
        const { id, latitude, longitude } = event; // Directly access event attributes

        if (!id || !latitude || !longitude) {
            console.error('Missing required attributes');
            return {
                statusCode: 400,
                body: JSON.stringify({ message: 'Missing required attributes' }),
            };
        }

        const timestamp = Date.now();

        const params = {
            TableName: 'Locations',
            Item: {
                id: { S: id },
                latitude: { N: String(latitude) },
                longitude: { N: String(longitude) },
                timestamp: { N: String(timestamp) }
            }
        };

        const command = new PutItemCommand(params);
        await dynamodbClient.send(command);

        return {
            statusCode: 200,
            body: JSON.stringify({ message: 'Location stored successfully' }),
        };
    } catch (error) {
        console.error('Error storing location:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: 'Failed to store location' }),
        };
    }
};


//next code

// index.mjs
import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';

const dynamodbClient = new DynamoDBClient({ region: 'us-east-1' });

export const handler = async (event) => {
    try {
        const { id, latitude, longitude } = event;

        if (!id || !latitude || !longitude) {
            console.error('Missing required attributes');
            return {
                statusCode: 400,
                body: JSON.stringify({ message: 'Missing required attributes' }),
            };
        }

        // Get current time
        const now = new Date();

        // Unix epoch time in seconds
        const timestamp = Math.floor(now.getTime() / 1000);

        // Human-readable date-time string
        const datetime = now.toISOString(); // Example: "2025-03-26T23:30:00.000Z"

        const params = {
            TableName: 'Locations',
            Item: {
                id: { S: id },
                latitude: { N: String(latitude) },
                longitude: { N: String(longitude) },
                timestamp: { N: String(timestamp) }, // Numeric timestamp for querying
                datetime: { S: datetime }            // Human-readable date-time
            }
        };

        const command = new PutItemCommand(params);
        await dynamodbClient.send(command);

        return {
            statusCode: 200,
            body: JSON.stringify({ message: 'Location stored successfully' }),
        };
    } catch (error) {
        console.error('Error storing location:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: 'Failed to store location' }),
        };
    }
};
//Working code latest

import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';

const dynamodbClient = new DynamoDBClient({ region: 'us-east-1' });

export const handler = async (event) => {
    try {
        const { email, name, latitude, longitude } = event;

        // Validate required attributes
        if (!email && !name) {
            console.error('Missing email or name');
            return {
                statusCode: 400,
                body: JSON.stringify({ message: 'Missing email or name' }),
            };
        }

        if (!latitude || !longitude) {
            console.error('Missing latitude or longitude');
            return {
                statusCode: 400,
                body: JSON.stringify({ message: 'Missing latitude or longitude' }),
            };
        }

        // Use email as id if provided, otherwise fallback to name
        const id = email || name;

        // Get current time
        const now = new Date();

        // Unix epoch time in seconds
        const timestamp = Math.floor(now.getTime() / 1000);

        // Separate date and time strings
        const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;

        const params = {
            TableName: 'Locations',
            Item: {
                id: { S: id },                     // Use email or name as the ID
                latitude: { N: String(latitude) },
                longitude: { N: String(longitude) },
                timestamp: { N: String(timestamp) }, // Numeric timestamp for querying
                date: { S: date },                  // Separate date column
                time: { S: time }                   // Separate time column
            }
        };

        const command = new PutItemCommand(params);
        await dynamodbClient.send(command);

        return {
            statusCode: 200,
            body: JSON.stringify({ message: 'Location stored successfully' }),
        };
    } catch (error) {
        console.error('Error storing location:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: 'Failed to store location' }),
        };
    }
};
