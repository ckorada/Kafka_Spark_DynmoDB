from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StringType, DoubleType, LongType
from pyspark.sql import Row
from decimal import Decimal
import boto3
import time

# Initialize Spark session
# spark = SparkSession.builder \
#     .appName("KafkaSparkDynamoDB") \
#     .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.dynamodb.catalog.DynamoCatalog") \
#     .getOrCreate()

spark = SparkSession.builder \
    .appName("KafkaSparkDynamoDB") \
    .config("spark.sql.catalog.dynamodb", "com.audienceproject.spark.dynamodb.catalog.DynamoDBCatalog") \
    .config("spark.sql.catalog.dynamodb.region", "us-east-2") \
    .getOrCreate()


# Define schema for the stock data
schema = StructType() \
    .add("Date", StringType()) \
    .add("Open", DoubleType()) \
    .add("High", DoubleType()) \
    .add("Low", DoubleType()) \
    .add("Close", DoubleType()) \
    .add("Volume", LongType())

# Kafka broker URL and topic name
kafka_brokers = "kafka:9092"
topic_name = "apple_stock_data"  # or any other topic name you use

# Read data from Kafka
stock_data = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_brokers) \
    .option("subscribe", topic_name) \
    .option("startingOffsets", "earliest") \
    .load()

# # Parse Kafka data and apply schema
# parsed_data = stock_data.selectExpr("CAST(value AS STRING)") \
#     .select(from_json(col("value"), schema).alias("data")) \
#     .select("data.*")

# Extract Kafka topic name
parsed_data = stock_data.selectExpr("CAST(topic AS STRING) as topic", "CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data"), "topic") \
    .select("data.*", "topic")

# Function to write data to DynamoDB
def write_to_dynamodb(batch_df, batch_id):
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')  # Use your AWS region
    print(dynamodb);
    table = dynamodb.Table('StockData')

    # Convert the Spark DataFrame to a Pandas DataFrame for easier processing
    pandas_df = batch_df.toPandas()
    i=0
    # Iterate over each row in the pandas DataFrame and insert into DynamoDB
    for index, row in pandas_df.iterrows():
        print(i);
        i+=1
        # Convert float values to Decimal
        table.put_item(
            Item={
                'timestamp': row['Date'],
                'open_price': Decimal(str(row['Open'])),
                'close_price': Decimal(str(row['Close'])),
                'high_price': Decimal(str(row['High'])),
                'low_price': Decimal(str(row['Low'])),
                'volume': int(row['Volume']),
                'topic_name': row['topic']  # Use dynamic topic name
            }
        )

# Write data to DynamoDB
query = parsed_data.writeStream \
    .outputMode("append") \
    .foreachBatch(write_to_dynamodb) \
    .start()

query.awaitTermination()
