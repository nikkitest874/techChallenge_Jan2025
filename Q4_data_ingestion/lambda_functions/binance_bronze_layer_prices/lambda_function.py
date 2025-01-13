import json
import requests
import boto3
import datetime
import os

# Binance API URL
BINANCE_API_URL = 'https://api.binance.com/api/v3/ticker/price'

# S3 Bucket Name (replace with your actual S3 bucket name)
S3_BUCKET_NAME = 'mybinance-test-bucket'

# Lambda Handler Function
def lambda_handler(event, context):
    # Define symbol for Binance API call (BTC/USDT in this case)
    # symbol = 'BTCUSDT'

    # Send GET request to Binance API
    response = requests.get(f"{BINANCE_API_URL}")

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
        output = []
        for i in data:
            price = i.get('price',None)
            symbol = i.get('symbol', None)
            s3_data = {
            'symbol': symbol,
            'price': price,
            'timestamp': timestamp}
            output.append(s3_data)  
        
        # Initialize S3 client
        s3_client = boto3.client('s3')

        # Generate a unique file name using the symbol and timestamp
        file_name = f"binance/ticker_prices/data_{timestamp}.json"
        
        # Convert the data to a JSON string and save it to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(output),
            ContentType='application/json'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data stored successfully in S3',
                'file': file_name
            })
        }
    else:
        return {
            'statusCode': response.status_code,
            'body': json.dumps({'error': 'Failed to fetch data from Binance API'})
        }
