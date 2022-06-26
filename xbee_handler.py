#
# Copyright (C) 2022 - Seyit Koyuncu, Kerim Güven (@akgvn) with some help from Berkay Apalı (@berkayapali)
#
# XBee data handling code for CanBee CanSat 2022 Ground Control System
#

from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QDialog, QFileDialog

def create_xbee_device(port):
    device = XBeeDevice(port, 9600)
    device.open()

    print("xbee.is_open():", device.is_open())

    return device

def send_data_with_xbee(device, device_to_send, data_to_send):
    device.send_data_async(device_to_send, data_to_send)

def read_from_xbee(device, container_data, payload_data,mqtt):
    xbee_message = device.read_data()

    if (xbee_message is not None): 
        data = xbee_message.data.decode("utf8").strip()

        if not (len(data) > 0):
            return 

        mqtt.send_mqtt_data(data)

        decode_csv(data, container_data, payload_data)

def decode_csv(csv, container_data, payload_data):
    data_list = csv.split(",")
    if not (len(data_list) > 0):
        print("---------------------", data_list)
        return
    print(data_list)

    data_conversion = [
        "ALTITUDE",  "TEMP",  "VOLTAGE", "TP_ALTITUDE",  "TP_TEMP",
         "TP_VOLTAGE",  "GYRO_R",  "GYRO_P",  "GYRO_Y",  "ACCEL_R",
         "ACCEL_P",  "ACCEL_Y",  "MAG_R",  "MAG_P",  "MAG_Y",  "POINTING_ERROR"
    ]
    
    index = 0
    if (data_list[3] == "C"):
        # Container data
        for key in container_data.keys():
            datum = data_list[index].strip()
            if key in data_conversion:
                if len(datum) > 0:
                    datum = float(datum)
                else:
                    datum = 0
            container_data[key].append(datum)
            index += 1
    elif (data_list[3] == "T"):
        # Payload data
        for key in payload_data.keys():
            datum = data_list[index].strip()
            if key in data_conversion:
                if len(datum) > 0:
                    datum = float(datum)
                else:
                    datum = 0
            payload_data[key].append(datum)
            index += 1
    else:
        print("Wrong Packet Type!!!")

# Sadece thread için
def read_from_xbee_loop(xbee, container_data, payload_data, mqtt):
    while True:
        read_from_xbee(xbee, container_data, payload_data,mqtt)
