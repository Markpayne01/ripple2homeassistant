# Ripple Energy MQTT Publisher

## Overview

This project integrates data from the Ripple Energy API into Home Assistant via MQTT. It periodically fetches data on energy generation and earnings from Ripple Energy, publishes the data to an MQTT broker, and provides Home Assistant discovery messages to automatically create sensors for tracking this data.

The program runs in two modes:

- **Loop mode**: Fetches data every 30 minutes.
- **Cron mode**: Fetches data once and exits, suitable for running via cron jobs.

## Key Features

- Fetches real-time data from the Ripple Energy API.
- Publishes data to an MQTT broker for integration into Home Assistant.
- Automatically creates sensors in Home Assistant using MQTT Discovery for fields like energy generation and earnings across multiple time windows (e.g., today, this week, this month, total).

## Requirements

Ensure the following dependencies are available:

- **Docker** 
- **MQTT broker** (e.g., Mosquitto)

### Python Packages

- requests
- paho-mqtt


## Environment Variables

The application requires several environment variables to be set for proper configuration. Below is a list of required variables:

| Environment Variable | Description | Example Value |
| --- | --- | --- |
| `RIPPLE_API_KEY` | API key for accessing the Ripple API | `your_api_key_here` |
| `MQTT_BROKER` | The address of the MQTT broker | `broker.address` |
| `MQTT_USERNAME` | MQTT username for authentication | `mqtt_user` |
| `MQTT_PASSWORD` | MQTT password for authentication | `mqtt_password` |
| `RUN_MODE` | Set to `loop` for periodic execution or `cron` to run once | `loop` or `cron`, optional, defaults to `loop`|

## Running the Application

### Docker Setup

You can run this application inside a Docker container. Below is an example of how to run the container with the required environment variables.

1.  Run the container with environment variables:
    
   ``` 
	docker run -d -e RIPPLE_API_KEY=your_api_key_here -e MQTT_BROKER=broker.address -e MQTT_USERNAME=mqtt_user -e MQTT_PASSWORD=mqtt_password -e RUN_MODE=loop ghcr.io/markpayne01/ripple2homeassistant/ripplemqttpublisher:latest
```
### Manual Python Setup

Alternatively, you can run the project locally by installing the dependencies and running the script.

1.  Install the dependencies:
        
 ```
  pip install requests paho-mqtt
```
    
2.  Set the environment variables and run the script:
        
```
export RIPPLE_API_KEY=your_api_key_here 
export MQTT_BROKER=mqtt://broker.address 
export MQTT_USERNAME=mqtt_user 
export MQTT_PASSWORD=mqtt_password 
python3 ripple_mqtt_publisher.py
```
    
