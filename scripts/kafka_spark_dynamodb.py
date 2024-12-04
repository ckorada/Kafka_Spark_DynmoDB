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
    .add("Volume", DoubleType())

# Kafka broker URL and topic name
kafka_brokers = "kafka:9092"
topic_apple = "apple_stock_data"  # or any other topic name you use
topic_twitter = "twitter_stock_data" 


# Read data from Kafka
apple_stock_data = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_brokers) \
    .option("subscribe", topic_apple) \
    .option("startingOffsets", "earliest") \
    .load()

# Read data from Kafka
twitter_stock_data = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_brokers) \
    .option("subscribe", topic_twitter) \
    .option("startingOffsets", "earliest") \
    .load()

# # Parse Kafka data and apply schema
# parsed_data = stock_data.selectExpr("CAST(value AS STRING)") \
#     .select(from_json(col("value"), schema).alias("data")) \
#     .select("data.*")

# Extract Kafka topic name
apple_parsed_data = apple_stock_data.selectExpr("CAST(topic AS STRING) as topic", "CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data"), "topic") \
    .select("data.*", "topic")

# Extract Kafka topic name
twitter_parsed_data = twitter_stock_data.selectExpr("CAST(topic AS STRING) as topic", "CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data"), "topic") \
    .select("data.*", "topic")

# Function to write data to DynamoDB
def write_to_dynamodb(batch_df, batch_id):
    # Create DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')  # Use your AWS region
    print(dynamodb);
    table = dynamodb.Table('StockDataAnalysis')

    # Convert the Spark DataFrame to a Pandas DataFrame for easier processing
    pandas_df = batch_df.toPandas()
    i=0
    # Iterate over each row in the pandas DataFrame and insert into DynamoDB
    for index, row in pandas_df.iterrows():
        print(i);
        i+=1
        composite_key = f"{row['Date']}_{row['topic']}"
        # Convert float values to Decimal
        table.put_item(
            Item={
                'timestamp_topic': composite_key,
                'timestamp': row['Date'],
                'open_price': Decimal(str(row['Open'])),
                'close_price': Decimal(str(row['Close'])),
                'high_price': Decimal(str(row['High'])),
                'low_price': Decimal(str(row['Low'])),
                'volume': Decimal(str(row['Volume'])),
                'topic_name': row['topic']  # Use dynamic topic name
            }
        )

# Write data to DynamoDB
apple_query = apple_parsed_data.writeStream \
    .outputMode("append") \
    .foreachBatch(write_to_dynamodb) \
    .start()

twitter_query = twitter_parsed_data.writeStream \
    .outputMode("append") \
    .foreachBatch(write_to_dynamodb) \
    .start()


twitter_query.awaitTermination()
apple_query.awaitTermination()
