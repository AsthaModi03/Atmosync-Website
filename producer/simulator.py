import random 
from datetime import datetime

containers={
    "A001": "Apple",
    "A002": "Mango",
    "A003": "Avocado"    
}

def generate_sensor_data():
    container_id=random.choice(list(containers.keys()))
    commodity=containers[container_id]
    if commodity=="Apple":
        temperature=round(random.uniform(2,6),2)
    elif commodity=="Mango":
        temperature=round(random.uniform(10,15),2)
    else:
        temperature=round(random.uniform(5,8),2)

    humidity= random.randint(75,95)
    data={
        "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "container_id":container_id,
        "commodity_type":commodity,
        "temperature_c":temperature,
        "humidity_pct":humidity,
        "gps_lat":round(random.uniform(20.0,30.0),6),
        "reading_id":random.randint(100000,999999),
        "anomaly":random.choice([0,1])
    }    

    return data