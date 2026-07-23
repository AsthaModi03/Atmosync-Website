from kafka import KafkaConsumer
import json

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