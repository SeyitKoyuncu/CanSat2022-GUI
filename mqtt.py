#
# Copyright (C) 2022 - Seyit Koyuncu, Kerim Güven (@akgvn)
#
# XBee data handling code for CanBee CanSat 2022 Ground Control System
#

import time, os
import paho.mqtt.client as mqtt

class MqttHandler:
    def __init__(self):
        # Define event callbacks
        def on_connect_callback(client, userdata, flags, rc):
            pass

        def on_message_callback(client, obj, msg):
            pass

        def on_publish_callback(client, obj, mid):
            pass

        def on_subscribe_callback(client, obj, mid, granted_qos):
            pass

        def on_log_callback(client, obj, level, string):
            pass

        self._mqttc = mqtt.Client()

        # Assign event callbacks
        self._mqttc.on_connect = on_connect_callback
        self._mqttc.on_message = on_message_callback
        self._mqttc.on_publish = on_publish_callback
        self._mqttc.on_subscribe = on_subscribe_callback # Uncomment to enable debug messages
        self._mqttc.on_log = on_log_callback

        self.topic = 'teams/1040'
        password = "Deetbevu221" # Secret!
        self._mqttc.username_pw_set("1040", password) # username and password for mqtt

        self._mqttc.connect("cansat.info", 1883) # use hostname and port to establish connection

    def send_mqtt_data(self, data):
        self._mqttc.publish(self.topic, data)
