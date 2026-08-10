from kafka import KafkaConsumer
import json
import snowflake.connector

conn=snowflake.connector.connect(
     user="RATATOUILLE11",

password="QWErtyuiop963258741",

account="UUBMYTG-TL42801",
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
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="atmosync-consumer-test",
    enable_auto_commit=True
)

print("Waiting for messages...\n")

for message in consumer:
    data = message.value

    print("Received:", data)

    cursor.execute("""
        INSERT INTO RAW_SENSOR_DATA_LIVE
        (
            TIMESTAMP,
            CONTAINER_ID,
            COMMODITY_TYPE,
            TEMPERATURE_C,
            HUMIDITY_PCT,
            GPS_LAT,
            GPS_LON,
            READING_ID,
            ANOMALY
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

    print("Inserted:", data)