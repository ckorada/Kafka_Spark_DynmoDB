from kafka import KafkaProducer
import pandas as pd
import json

# Configure Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9093',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Topics for datasets
apple_topic = 'apple_stock_data'
twitter_topic = 'twitter_stock_data'

# Function to send dataset to Kafka
def produce_data(file_path, topic_name):
    # Read dataset
    data = pd.read_csv(file_path)
    for index, row in data.iterrows():
        message = row.to_dict()
        producer.send(topic_name, message)
        print(f"Sent to {topic_name}: {message}")

# Produce Apple and Twitter datasets
produce_data('AAPL.csv', apple_topic)
produce_data('twitter-stocks.csv', twitter_topic)
