import boto3
import io
import pandas as pd
import numpy as np

import json
import os
import sys
import importlib
import logging
import subprocess


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # S3 bucket and folder
    bucket_name = 'mybinance-test-bucket'
    data_source = 'binance'
    folder_prefix = 'ticker_prices'
    silver_bucket = 'mybinance-silver-bucket'

    # Initialize S3 client
    s3 = boto3.client('s3')

    try:
        # List objects in the folder
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=f'{data_source}/{folder_prefix}')
        
        # Check if the folder is empty
        if 'Contents' not in response:
            return {
                "statusCode": 404,
                "body": "No files found in the specified folder."
            }

        # Find the latest file based on LastModified timestamp
        latest_file = max(
            response['Contents'], key=lambda x: x['LastModified']
        )
        latest_file_key = latest_file['Key']

        # Fetch the latest file's content
        file_object = s3.get_object(Bucket=bucket_name, Key=latest_file_key)
        file_content = file_object['Body'].read().decode('utf-8')

         # Parse the JSON content
        try:
            data = json.loads(file_content)  # Assuming it's a JSON file with a list of dictionaries
        except json.JSONDecodeError as e:
            return {
                "statusCode": 500,
                "body": f"Failed to parse JSON: {e}"
            }

        # Convert the list of dictionaries into a DataFrame
        df = pd.DataFrame(data)
        print(df.head())
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)

        file_name = latest_file_key.rpartition('/')[-1].replace('.json','.csv')
        file_key = f'binanceSilver/{folder_prefix}/{file_name}'

        try:
            # Write CSV to S3
            s3.put_object(Bucket=silver_bucket, Key=file_key, Body=csv_buffer.getvalue())
            print(f"File successfully written to s3://{bucket_name}/{file_key}")
            return {
                "statusCode": 200,
                "body": f"File successfully written to s3://{bucket_name}/{file_key}"
            }
        except Exception as e:
            print(f"Error writing file to S3: {e}")
            return {
                "statusCode": 500,
                "body": str(e)
            }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": str(e)
        }
