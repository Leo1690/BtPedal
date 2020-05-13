# coding=utf-8
#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
import bluetooth
import pyautogui
import threading
from time import sleep
import csv
import Parameters as pr

root = tk.Tk()
server_sock = None
port = None
client_sock = None

def on_closing():
    with open(pr.fPath, 'wt') as f:
        writer = csv.writer(f, delimiter =' ');
        writer.writerow([pr.aSensitivity,pr.aThreshold,pr.cFilter,pr.keyForward]);
    pr.running=False
    pr.killSystem=True
    root.destroy()

def startBt():
    global server_sock, port, client_sock
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]
    bluetooth.advertise_service(server_sock, "SampleServer", service_id=pr.uuid,
                                service_classes=[pr.uuid, bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])
    server_sock.settimeout(2)
    client_sock, client_info = server_sock.accept()

def readAcc():
    global client_sock
    try:
        while pr.running:
            data = client_sock.recv(1)
            if not data:
                break
            if len(data)>0:
                pr.rAcc = pr.cFilter*pr.rAcc+(1-pr.cFilter)*ord(data)
                if abs(pr.cAcc-pr.rAcc)>pr.aSensitivity:
                    pr.cAcc=pr.rAcc 
    except:
        pr.running=False;
    pr.rAcc = 0;
    try:
        client_sock.close()
        server_sock.close()
    except:
        pass
    
def controlAcc():
    while pr.running:
        if not pr.racing and pr.cAcc>=pr.aThreshold:
            pr.racing=True;
            pyautogui.keyDown(pr.keyForward);
        elif pr.racing and pr.cAcc<pr.aThreshold:
            pr.racing=False;
            pyautogui.keyUp(pr.keyForward);
        else:
            sleep(0.05)

       
class EcoderGUI:
    
    def readEntry(self,a,b):
        try:
            b=a.get()
        except:
            a.set(b)
        return b   

    def readParameters(self):
        pr.keyForward = self.readEntry(self.keyForwardTk,pr.keyForward)
        pr.cFilter = self.readEntry(self.cFilterTk,pr.cFilter)
        pr.aSensitivity = self.readEntry(self.aSensitivityTk,pr.aSensitivity)
        pr.aThreshold = self.readEntry(self.aThresholdTk,pr.aThreshold)
        
    def listenBt(self):
        while not pr.killSystem:
            while not pr.running:
                try:
                    startBt()
                    pr.running=True
                except:
                    pr.running=False
                    break
            if pr.running:   
                self.readParameters()
                controlAccThread=threading.Thread(target=controlAcc, args=())
                controlAccThread.start()
                checkStateThread=threading.Thread(target=self.checkState, args=())
                checkStateThread.start()
                readAcc()
                controlAccThread.join()
                checkStateThread.join()
        
    def loadParameters(self):
        reader = csv.reader(open(pr.fPath, "rt"), delimiter=' ');
        l = list(reader);
        self.aSensitivityTk.set(l[0][0])
        self.aThresholdTk.set(l[0][1])
        self.cFilterTk.set(l[0][2])
        self.keyForwardTk.set(l[0][3])
        self.readParameters()
        
    def changeStateEntry(self,newState):
        self.aSensitivityEntry.config(state=newState)
        self.aThresholdEntry.config(state=newState)
        self.cFilterEntry.config(state=newState)
        self.keyForwardEntry.config(state=newState)
    
    def checkState(self):
        self.changeStateEntry('disabled')
        self.stateLabel.config(text="Connected")  
        while pr.running:
            self.accLabel.config(text=str(round(pr.rAcc,2)))
            sleep(0.2)
        try:
            self.accLabel.config(text="---")
            self.changeStateEntry('normal')
            self.stateLabel.config(text="Disconnected")  
        except:
            pass
                
    def playAction(self):
        global server_sock
        if not pr.running:
            pr.running=True
            self.readParameters()
            startBt()
            self.controlAccThread=threading.Thread(target=controlAcc, args=())
            self.controlAccThread.start()
            self.readAccThread=threading.Thread(target=readAcc, args=())
            self.readAccThread.start()
            self.checkStateThread=threading.Thread(target=self.checkState, args=())
            self.checkStateThread.start()
        else:
            pr.running=False

    def createVariables(self):
        self.keyForwardTk = tk.StringVar()
        self.aThresholdTk = tk.IntVar()
        self.aSensitivityTk = tk.IntVar()
        self.cFilterTk = tk.DoubleVar()

    def createElements(self):
        self.content=ttk.Frame(self.master, padding = 5)
        self.keyForwardEntry=ttk.Entry(self.content,textvariable=self.keyForwardTk)
        self.aThresholdEntry=ttk.Entry(self.content,textvariable=self.aThresholdTk)
        self.aSensitivityEntry=ttk.Entry(self.content,textvariable=self.aSensitivityTk)
        self.cFilterEntry=ttk.Entry(self.content,textvariable=self.cFilterTk)
        self.stateLabel=ttk.Label(self.content, text = 'Disconnected')
        self.accLabel=ttk.Label(self.content, text = "---")
        self.keyForwardLabel=ttk.Label(self.content, text = 'Key')
        self.aThresholdLabel=ttk.Label(self.content, text = 'Threshold')
        self.aSensitivityLabel=ttk.Label(self.content, text = 'Sensitivity')
        self.cFilterLabel=ttk.Label(self.content, text = 'Filter')

    def placeElements(self):
        self.content.grid(column = 0, row = 0, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.keyForwardEntry.grid(column = 0, row = 0, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.keyForwardLabel.grid(column = 1, row = 0, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.aThresholdEntry.grid(column = 0, row = 1, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.aThresholdLabel.grid(column = 1, row = 1, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.aSensitivityEntry.grid(column = 0, row = 2, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.aSensitivityLabel.grid(column = 1, row = 2, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.cFilterEntry.grid(column = 0, row = 3, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.cFilterLabel.grid(column = 1, row = 3, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.stateLabel.grid(column = 0, row = 4, sticky = (tk.N, tk.S, tk.E, tk.W))
        self.accLabel.grid(column = 1, row = 4, sticky = (tk.N, tk.S, tk.E, tk.W))
 
    def configCells(self):
        self.master.columnconfigure(0, weight = 1) 
        self.master.rowconfigure(0, weight = 1)
        self.content.columnconfigure(1, weight = 1) 
        self.content.rowconfigure(0, weight = 1)
          
    def __init__(self,master):
        self.master=master      
        self.createVariables()
        self.createElements()
        self.placeElements()
        self.configCells()
        self.loadParameters()
        listenBtThread=threading.Thread(target=self.listenBt, args=())
        listenBtThread.start()
             
app = EcoderGUI(root)
root.title('BtPedal')

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()