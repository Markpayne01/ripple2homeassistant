import json
import requests
import time
import logging
import os  # For accessing environment variables
import paho.mqtt.client as mqtt

# Fetching configuration from environment variables
API_KEY = os.getenv("RIPPLE_API_KEY")
RIPPLE_API_URL = f"https://rippleenergy.com/rest/member_data/{API_KEY}"
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = 1883
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
RUN_MODE = os.getenv("RUN_MODE", "loop")  # 'loop' is default, 'cron' runs once and exits

# Home Assistant MQTT discovery prefix
HA_DISCOVERY_PREFIX = "homeassistant"

# MQTT topics (Farm name will be dynamically fetched)
GENERATION_TOPIC_TEMPLATE = "ripple/{farm_name}/{time_window}/state"
EARNED_TOPIC_TEMPLATE = "ripple/{farm_name}/{time_window}/earned_state"
DISCOVERY_TOPIC_TEMPLATE = "{prefix}/sensor/{farm_name}/{time_window}_{field}/config"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize MQTT client
client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Function to fetch Ripple Energy data
def fetch_ripple_data():
    try:
        response = requests.get(RIPPLE_API_URL)
        response.raise_for_status()  # Raise an error if the request fails
        logging.info("Successfully fetched data from Ripple Energy API.")
        return response.json()  # Assuming the API returns a JSON response
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None

# Function to publish Home Assistant discovery payloads for both generated and earned fields
def publish_discovery(farm_name, time_window):
    # Discovery config for generated field
    generated_config = {
        "name": f"{farm_name} {time_window.capitalize()} Generated".replace('_', ' ').title(),
        "state_topic": GENERATION_TOPIC_TEMPLATE.format(farm_name=farm_name, time_window=time_window),
        "unit_of_measurement": "kWh",
        "device_class": "energy",
        "state_class": "total",
        "value_template": "{{ value_json.generated }}",
        "unique_id": f"{farm_name}_{time_window}_generated"
    }

    # Discovery config for earned field
    earned_config = {
        "name": f"{farm_name} {time_window.capitalize()} Earned".replace('_', ' ').title(),
        "state_topic": EARNED_TOPIC_TEMPLATE.format(farm_name=farm_name, time_window=time_window),
        "unit_of_measurement": "GBP",
        "device_class": "monetary",
        "state_class": "total",
        "value_template": "{{ value_json.earned }}",
        "unique_id": f"{farm_name}_{time_window}_earned"
    }

    # Publish discovery messages for both generated and earned fields
    discovery_topic_generated = DISCOVERY_TOPIC_TEMPLATE.format(prefix=HA_DISCOVERY_PREFIX, farm_name=farm_name, time_window=time_window, field="generated")
    discovery_topic_earned = DISCOVERY_TOPIC_TEMPLATE.format(prefix=HA_DISCOVERY_PREFIX, farm_name=farm_name, time_window=time_window, field="earned")
    
    client.publish(discovery_topic_generated, json.dumps(generated_config), retain=True)
    client.publish(discovery_topic_earned, json.dumps(earned_config), retain=True)
    
    logging.info(f"Published discovery message for {time_window.capitalize()} Generated: {discovery_topic_generated} - {json.dumps(generated_config)}")
    logging.info(f"Published discovery message for {time_window.capitalize()} Earned: {discovery_topic_earned} - {json.dumps(earned_config)}")

# Function to publish the latest generation and earned data to MQTT for each time window
def publish_data(farm_name, generation_data):
    # Time windows to publish (based on API structure)
    time_windows = [
        "today", "yesterday", "this_week", "last_week",
        "this_month", "last_month", "this_year", "last_year", "total"
    ]

    # Loop through each time window and publish its data
    for window in time_windows:
        window_data = generation_data.get(window, {})
        generated = window_data.get("generated", 0)
        earned = window_data.get("earned", 0)

        # Publish generation data
        generation_topic = GENERATION_TOPIC_TEMPLATE.format(farm_name=farm_name, time_window=window)
        client.publish(generation_topic, json.dumps({"generated": generated}))
        logging.info(f"Published {window} generation to MQTT: {generation_topic} - {json.dumps({'generated': generated})}")

        # Publish earned data
        earned_topic = EARNED_TOPIC_TEMPLATE.format(farm_name=farm_name, time_window=window)
        client.publish(earned_topic, json.dumps({"earned": earned}))
        logging.info(f"Published {window} earned to MQTT: {earned_topic} - {json.dumps({'earned': earned})}")

# Main function to fetch data and publish to MQTT
def main():
    # Fetch the latest data from Ripple API
    data = fetch_ripple_data()

    if data:
        # Extract the farm name and generation data
        generation_assets = data.get("generation_assets", [])
        for farm in generation_assets: 
            farm_name = farm.get("name").replace(" ", "_").lower()
            generation_data = farm.get("generation", {})

            # Publish discovery config for all time windows
            time_windows = [
                "today", "yesterday", "this_week", "last_week",
                "this_month", "last_month", "this_year", "last_year", "total"
            ]
            for window in time_windows:
                publish_discovery(farm_name, window)
            time.sleep(1)  # Waiting a moment for Home Assistant to discover the new sensors
            
            # Publish the latest data for each time window
            publish_data(farm_name, generation_data)
    else:
        logging.error("Failed to fetch data from the API.")

# Main loop to periodically fetch data and publish to MQTT
if __name__ == "__main__":
    if RUN_MODE == "cron":
        # Run once if running via cron
        logging.info("Running in cron mode: Fetching data and exiting.")
        main()
    else:
        # Default mode: loop forever
        logging.info("Running in loop mode: Fetching data periodically.")
        while True:
            main()
            time.sleep(1800)  # Sleep for 30 minutes before fetching data again
