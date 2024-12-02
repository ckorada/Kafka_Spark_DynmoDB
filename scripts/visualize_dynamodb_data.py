import boto3
import matplotlib.pyplot as plt
from datetime import datetime
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')  # Replace with your region
table = dynamodb.Table('StockData')  # Replace with your table name

# Fetch data for a specific topic
def fetch_data_by_topic(topic_name):
    response = table.scan(
        FilterExpression='topic_name = :topic',
        ExpressionAttributeValues={':topic': topic_name}
    )
    return response['Items']

# Process data for visualization
def process_data(data):
    timestamps = []
    open_prices = []
    close_prices = []
    high_prices = []
    low_prices = []
    volumes = []

    for item in data:
        timestamps.append(datetime.strptime(item['timestamp'], '%Y-%m-%d'))
        open_prices.append(float(item['open_price']))
        close_prices.append(float(item['close_price']))
        high_prices.append(float(item['high_price']))
        low_prices.append(float(item['low_price']))
        volumes.append(int(item['volume']))

    return timestamps, open_prices, close_prices, high_prices, low_prices, volumes

# Visualize data
def visualize_data(timestamps, open_prices, close_prices, high_prices, low_prices, volumes, topic_name):
    plt.figure(figsize=(14, 8))

    # Plot open and close prices
    plt.plot(timestamps, open_prices, label='Open Price', marker='o')
    plt.plot(timestamps, close_prices, label='Close Price', marker='x')

    # Highlight high and low prices
    plt.fill_between(timestamps, low_prices, high_prices, color='gray', alpha=0.2, label='High-Low Range')

    # Set title and labels
    plt.title(f'Trend Analysis for Topic: {topic_name}', fontsize=16)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Price', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid()

    plt.tight_layout()
    plt.show()



