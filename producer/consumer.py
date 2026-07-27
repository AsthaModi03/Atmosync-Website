from kafka import KafkaConsumer
import json
import snowflake.connector

conn=snowflake.connector.connect(
     user="BHUMI123",

password="gGkAZLfRNK8pRp6",

account="FIFIAPE-KZ59572",
      warehouse="COMPUTE_WH",
      database="ATMOSYNC_DB",
      schema="PUBLIC"
)

cursor = conn.cursor()
print("Connected to Snowflake!")

cursor.execute("SELECT CURRENT_VERSION();")
print(cursor.fetchone())
consumer = KafkaConsumer(
    "sensor_data",

bootstrap_servers="localhost:9092",
     value_deserializer=lambda m:
json.loads(m.decode("utf-8")),
     auto_offset_reset="earliest"
)

print("Waiting for messages...\n")

for message in consumer:
    print(message.value)