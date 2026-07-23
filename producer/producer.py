from kafka import KafkaProducer
import pandas as pd
import json 
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v:
    json.dumps(v).encode('utf-8')
)

df = pd.read_csv("Data/processed/sensor_data.csv")

for _, row in df.iterrows():
    producer.send("sensor_data",row.to_dict())
    print(row.to_dict())
    time.sleep(1)

producer.flush()
print("Data streaming completed!")