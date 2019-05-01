"""
    Program to read and save data from Sensirion SPS30 sensor

    Written by
    Szymon Jakubiak
    Central Institute for Labour Protection - National Research Institute
    Department of Chemical, Aerosol and Biological Hazards
    Aerosols, Filtration and Ventilation Laboratory
    Warsaw, Poland
    szymon.jakubiak@ciop.pl

    Units for measurements:
        PM1, PM2.5, PM4 and PM10 are in ug/m^3, numerical concentrations are in #/cm^3
"""
import serial, struct, time

# Specify serial port name for sensor
device_port = "COM48"

# Specify output file name and comment about experiment
output_file = "SPS30-1.txt"
comment = "Experiment ID"

class SPS30:
    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(self.port, baudrate=115200, stopbits=1, parity="N",  timeout=2)
    
    def start(self):
        self.ser.write([0x7E, 0x00, 0x00, 0x02, 0x01, 0x03, 0xF9, 0x7E])
        
    def stop(self):
        self.ser.write([0x7E, 0x00, 0x01, 0x00, 0xFE, 0x7E])
    
    def read_values(self):
        self.ser.flushInput()
        self.ser.write([0x7E, 0x00, 0x03, 0x00, 0xFC, 0x7E])
        toRead = self.ser.inWaiting()
        while toRead < 47:
            toRead = self.ser.inWaiting()
            time.sleep(0.1)
        raw = self.ser.read(toRead)
        
        # Reverse byte-stuffing
        if b'\x7D\x5E' in raw:
            raw = raw.replace(b'\x7D\x5E', b'\x7E')
        if b'\x7D\x5D' in raw:
            raw = raw.replace(b'\x7D\x5D', b'\x7D')
        if b'\x7D\x31' in raw:
            raw = raw.replace(b'\x7D\x31', b'\x11')
        if b'\x7D\x33' in raw:
            raw = raw.replace(b'\x7D\x33', b'\x13')
        
        # Discard header and tail
        rawData = raw[5:-2]
        
        try:
            data = struct.unpack(">ffffffffff", rawData)
        except struct.error:
            data = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return data

    def close_port(self):
        self.ser.close()

# Create a header in file with output data
date = time.localtime()
date = str(date[2]) + "." + str(date[1]) + "." + str(date[0])
header = "\n" + "* * * *\n\n" + date
if len(comment) > 0:
    header += "\n" + comment
header += "\n\n" + "* * * *\n\n"
header += "Date,Time,SPS30\n"
header += "dd:mm:yyyy,hh:mm:ss,Mass,,,,Numerical\n"
header += ",,PM1,PM2.5,PM4,PM10,0.3÷0.5,0.3÷1,0.3÷2.5,0.3÷4,0.3÷10,typical size\n"
header += ",,ug/m^3,ug/m^3,ug/m^3,ug/m^3,#/cm^3,#/cm^3,#/cm^3,#/cm^3,#/cm^3,um\n"
print(header)
file = open(output_file, "a")
file.write(header)
file.close()

sensor = SPS30(device_port)
sensor.start()
time.sleep(5)

try:
    while True:
        output = sensor.read_values()
        sensorData = ""
        for val in output:
            sensorData += "{0:.2f},".format(val)
        date = time.localtime()
        act_date = str(date[2]) + "." + str(date[1]) + "." + str(date[0])
        act_time = str(date[3]) + ":" + str(date[4]) + ":" + str(date[5])

        output_data = act_date + "," + act_time + "," + sensorData[:-1] # remove comma from the end
        
        file = open(output_file, "a")
        file.write(output_data + "\n")
        file.close()
        print(output_data)

        time.sleep(1)

except KeyboardInterrupt:
    sensor.close_port()
    print("Data logging stopped")
