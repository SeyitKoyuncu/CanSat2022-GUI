#
# Copyright (C) 2022 - Seyit Koyuncu -- with some help from Kerim Güven (@akgvn)
#
# GUI code for CanBee CanSat 2022 Ground Control System
#

from secrets import choice
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QDialog, QFileDialog
from pyqtgraph import PlotWidget, plot
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from random import randint
import serial.tools.list_ports
import numpy as np
import sys  
import os
import time
import random
import logging
import json

from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress
import threading
import xbee
import xbee_handler
import mqtt

# CanSAT'ın yolladığı CSV'nin içerdiği simulated pressure data'sı
sim_data = [
    100770, 100773, 100796, 100803, 100807, 100760, 100804, 100765, 100792, 100795,
    98252, 96975, 95546, 94429, 93569, 92870, 92373, 91970, 91741, 91929, 92072,
    92213, 92410, 92591, 92751, 92903, 93096, 93260, 93392, 93588, 93761, 93911,
    94083, 94238, 94425, 94604, 94764, 94952, 95098, 95280, 95462, 95605, 95736, 
    95879, 95996, 96120, 96284, 96391, 96533, 96643, 96696, 96781, 96861, 96942, 
    97034, 97143, 97186, 97273, 97347, 97450, 97526, 97617, 97713, 97802, 97866,
    97944, 98000, 98086, 98173, 98286, 98365, 98417, 98495, 98588, 98697, 98758,
    98845, 98905, 99019, 99107, 99200, 99266, 99333, 99418, 99513, 99579, 99665,
    99759, 99834, 99930, 99997, 100080, 100163, 100244, 100344, 100436, 100485, 100608,
    100680, 100734, 100852, 100862, 100862, 100815, 100841, 100838, 100864, 100833,
    100837, 100840, 100838, 100838, 100838, 100838, 100838, 100838, 100838
]

def sim_pressure_data(xbee):
        container_address = "0013A200418DAC90"
        container_remote = RemoteXBeeDevice(xbee, XBee64BitAddress.from_hex_string(container_address))

        for simData in sim_data:
            xbee.send_data(container_remote, str("SIMP" + str(simData)))
            time.sleep(1) # bir saniye beklenecek diyorum

class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page   
        uic.loadUi('MainUI.ui', self)

        self.xbee = None

        try:
            self.mqtt = mqtt.MqttHandler()

        except:
            print("Cant connect mqttt connection...")
            print("Cant connect mqttt connection...")
            pass

        self.SIM_ON = False
        self.done = False

        self.container_data = {
            "TEAM_ID": [],
            "MISSION_TIME": [],
            "PACKET_COUNT": [],
            "PACKET_TYPE": [],
            "MODE": [],
            "TP_RELEASED": [],
            "ALTITUDE": [],
            "TEMP": [],
            "VOLTAGE": [],
            "GPS_TIME": [],
            "GPS_LATITUDE": [],
            "GPS_LONGITUDE": [],
            "GPS_ALTITUDE": [],
            "GPS_SATS": [],
            "SOFTWARE_STATE": [],
            "CMD_ECHO": []
        }

        self.payload_data = {
            "TEAM_ID": [],
            "MISSION_TIME": [],
            "PACKET_COUNT": [],
            "PACKET_TYPE": [],
            "TP_ALTITUDE":[],
            "TP_TEMP": [],
            "TP_VOLTAGE": [],
            "GYRO_R": [],
            "GYRO_P": [],
            "GYRO_Y":[],
            "ACCEL_R": [],
            "ACCEL_P": [],
            "ACCEL_Y": [],
            "MAG_R": [],
            "MAG_P": [],
            "MAG_Y": [],
            "POINTING_ERROR": [],
            "TP_SOFTWARE_STATE": []
        }

        self.pen = pg.mkPen(color=(255, 0, 0))

        self.data_and_graph_widgets = [
            (self.container_data["ALTITUDE"],     self.graphWidget), 
            (self.container_data["TEMP"],         self.graphWidget2), 
            (self.container_data["VOLTAGE"],      self.graphWidget3),
            # Payload:
            (self.payload_data["TP_ALTITUDE"],    self.graphWidget4), 
            (self.payload_data["TP_TEMP"],        self.graphWidget5), 
            (self.payload_data["TP_VOLTAGE"],     self.graphWidget6), 
            (self.payload_data["GYRO_R"],         self.graphWidget7),
            (self.payload_data["GYRO_P"],         self.graphWidget8),
            (self.payload_data["GYRO_Y"],         self.graphWidget9),
            (self.payload_data["ACCEL_R"],        self.graphWidget10),
            (self.payload_data["ACCEL_P"],        self.graphWidget11),
            (self.payload_data["ACCEL_Y"],        self.graphWidget12),
            (self.payload_data["MAG_R"],          self.graphWidget13),
            (self.payload_data["MAG_P"],          self.graphWidget14),
            (self.payload_data["MAG_Y"],          self.graphWidget15),
            (self.payload_data["POINTING_ERROR"], self.graphWidget16), 
        ]

        self.timer = QtCore.QTimer()
        self.timer.setInterval(200) #give change of graph speed
        self.timer.timeout.connect(self.update_plot_data)

        self.SendButton.clicked.connect(self.SendButtonClicked)
        self.BrowseButton.clicked.connect(self.BrowseClicked)
        # self.SendPathButton.clicked.connect(self.SendPath) # TODO Bu tuşa artık gerek yok gibi
        self.check_ports_button.clicked.connect(self.CheckPorts)
        self.sendport_button.clicked.connect(self.SelectPort)
        self.sim_toggle_button.clicked.connect(self.ChangeSIM)
        self.send_simdata_button.clicked.connect(self.send_sim_pressure_data)
        #self.reset_button

        self.path = " " 
        self.count = 0
        self.send_sim = None

        self.comboBox2.addItem("1")
        self.comboBox2.addItem("2")

        #LABELS
        self.graphWidget.setTitle("TP_ALTITUDE")
        self.graphWidget2.setTitle("TP_TEMP")
        self.graphWidget3.setTitle("VOLTAGE")
        self.graphWidget4.setTitle("TP_ALTITUDE")
        self.graphWidget5.setTitle("TP_TEMP")
        self.graphWidget6.setTitle("TP_VOLTAGE")
        self.graphWidget7.setTitle("GYRO_R")
        self.graphWidget8.setTitle("GYRO_P")
        self.graphWidget9.setTitle("GYRO_Y")
        self.graphWidget10.setTitle("ACCEL_R")
        self.graphWidget11.setTitle("ACCEL_P")
        self.graphWidget12.setTitle("ACCEL_Y")
        self.graphWidget13.setTitle("MAG_R")
        self.graphWidget14.setTitle("MAG_P")
        self.graphWidget15.setTitle("MAG_Y")
        self.graphWidget16.setTitle("POINTING_ERROR")

        #comboBox_command add elements
        keys_command =[
            "CX ON",
            "CX OFF",
            "TP ON",
            "TP OFF",
            "PRCHUTE",
            "RELEASE",
            "CAM ON",
            "CAM OFF",
            "BUZ ON",
            "BUZ OFF",
            "SIM ON",
            "SIMOFF",
            "SIMP"
        ]

        for key in keys_command:
            self.comboBox_command.addItem(key)
        
    def ChangeSIM(self):
        self.SIM_ON = not self.SIM_ON
        self.mqtt.send_mqtt_data("SIM ON")
        print("self.SIM_ON is", self.SIM_ON)


    def send_sim_pressure_data(self):
        if self.send_sim != None:
            return

        self.send_sim = threading.Thread(
            target = sim_pressure_data,
            args   = (self.xbee,)
        )

        self.send_sim.start()
        print("SIM THREAD STARTED")


    def SelectPort(self):
        port = self.comboBox.currentText()
        self.xbee = xbee_handler.create_xbee_device(port)

        print("xbee.is_open():", self.xbee.is_open())
 
        self.xbee_receive_thread = threading.Thread(
            target = xbee_handler.read_from_xbee_loop,
            args   = (self.xbee, self.container_data, self.payload_data, self.mqtt,)
        )

        self.xbee_receive_thread.start()
        self.timer.start()

    def CheckPorts(self):
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            if ("PID=0403:6001" in hwid): # Xbee PID
                self.comboBox.addItem(port)

    def BrowseClicked(self):
        #QFileDialog.getOpenFileName(title, starting path, optinial = searching file type)
        file = QFileDialog.getOpenFileName(self,'Open file','D:')
        self.path = file[0]
        self.PathLineEdit.setText(self.path)

    def SendButtonClicked(self):
        data = self.comboBox_command.currentText()
        payload = RemoteXBeeDevice(self.xbee, XBee64BitAddress.from_hex_string("0013A200410A4EC7"))
        container = RemoteXBeeDevice(self.xbee, XBee64BitAddress.from_hex_string("0013A200418DAC90"))
        xbee_handler.send_data_with_xbee(self.xbee, container, data)
        xbee_handler.send_data_with_xbee(self.xbee, payload, data)

    def update_plot_data(self):
        #if self.done:
        #    return
        #for (data, widget) in self.data_and_graph_widgets:
        #    if len(data) > 10:
        #        self.done = True
        #    elif len(data) > 0:
        #        widget.plot(y = data, pen = self.pen)
        pass
        

#def main():
app = QtWidgets.QApplication(sys.argv)
main = MainWindow() 

main.show()
sys.exit(app.exec_())   

#if __name__ == '__main__':
    #main()

