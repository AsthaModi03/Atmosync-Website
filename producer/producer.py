from kafka import KafkaProducer
from simulator import generate_sensor_data
import json 
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v:
    json.dumps(v).encode('utf-8')
)
 
while True:
    data = generate_sensor_data()

    producer.send("sensor_data",data)
    producer.flush()
    print(data)
    time.sleep(2)