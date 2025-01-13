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
    data_source = 'binanceSilver'
    folder_prefix = 'ticker_prices'
    silver_bucket = 'mybinance-silver-bucket'
    
    output_folder = 'binanceGold/ticker_prices_hist'
    gold_bucket = 'mybinance-gold-bucket'

    target_crypto = 'BTCUSDT'

    # Initialize S3 client
    s3 = boto3.client('s3')

    try:
        # List objects in the folder
        response = s3.list_objects_v2(Bucket=silver_bucket, Prefix=f'{data_source}/{folder_prefix}')
        
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
        new_object = s3.get_object(Bucket=silver_bucket, Key=latest_file_key)
        new_content = new_object['Body'].read().decode('utf-8')

        data = pd.read_csv(io.StringIO(new_content))
        filtered = data[data['symbol'] == target_crypto]
        filtered['crypto'] = filtered['symbol'].str.strip()
        filtered['name'] = 'Bitcoin Tether USDT'
        filtered['effective_at'] = filtered['timestamp'].str[:10] + ' ' + filtered['timestamp'].str[11:19].str.replace('-',':')

        df = filtered[['crypto', 'name', 'price', 'effective_at']]

        df = df.sort_values(by="effective_at").drop_duplicates(subset=["crypto"], keep="last")

        print('new data fetched and transformed!')


    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": str(e)
        }

    # fetch the historical data from gold folder
    try:
        # List objects in the folder
        response = s3.list_objects_v2(Bucket=gold_bucket, Prefix=f'{output_folder}/{target_crypto}')
        
        # Check if the folder is empty
        if 'Contents' not in response:
            full_data = df
        else:
            # Find the latest file based on LastModified timestamp
            current_hist_file = max(
            response['Contents'], key=lambda x: x['LastModified'])
            current_hist = current_hist_file['Key']
            
            # Fetch the latest file's content
            current_data = s3.get_object(Bucket=gold_bucket, Key=current_hist)
            current_content = current_data['Body'].read().decode('utf-8')

            hist_df = pd.read_csv(io.StringIO(current_content))
            full_data = pd.concat([hist_df, df], ignore_index=True)
            full_data = full_data.drop_duplicates()


        csv_buffer = io.StringIO()
        full_data.to_csv(csv_buffer, index=False)
        file_key = f'{output_folder}/{target_crypto}/price_history.csv'

        try:
            # Write CSV to S3
            s3.put_object(Bucket=gold_bucket, Key=file_key, Body=csv_buffer.getvalue())
            print(f"File successfully written to s3://{gold_bucket}/{file_key}")
            return {
                "statusCode": 200,
                "body": f"File successfully written to s3://{gold_bucket}/{file_key}"
            }
        except Exception as e:
            print(f"Error writing file to S3: {e}")
            return {
                "statusCode": 500,
                "body": str(e)}

    except Exception as e:
        print(f"Error writing file to S3: {e}")
        return {
                "statusCode": 500,
                "body": str(e)
            }
