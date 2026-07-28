from kafka import KafkaConsumer
import json
import snowflake.connector

conn=snowflake.connector.connect(
    user="RATATOUILLE11",
    password="QWEpoi963147852",
    account="UUBMYTG-TL42801",
    warehouse="COMPUTE_WH",
    database="ATMOSYNC_DB",
    schema="PUBLIC",
       
)
cursor = conn.cursor()

# -----------------------------
# Kafka Consumer
# -----------------------------
consumer = KafkaConsumer(
    "sensor_data",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest"
)

print("Listening for Kafka messages...")

for message in consumer:
    data = message.value

    print(data)

    cursor.execute("""
        INSERT INTO RAW_SENSOR_DATA
        (
            timestamp,
            container_id,
            commodity_type,
            temperature_c,
            humidity_pct,
            gps_lat,
            gps_lon,
            reading_id,
            anomaly
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["timestamp"],
        data["container_id"],
        data["commodity_type"],
        data["temperature_c"],
        data["humidity_pct"],
        data["gps_lat"],
        data["gps_lon"],
        data["reading_id"],
        data["anomaly"]
    ))

    conn.commit()

print("Finished")