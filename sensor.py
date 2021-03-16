import socket
import time
import asyncio
import time
import json
import os
import sys

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import Twin, TwinProperties, QuerySpecification, QueryResult

IOTHUB_CONNECTION_STRING = "HostName=programming-arduino.azure-devices.net;SharedAccessKeyName=service;SharedAccessKey=B0niIYnIrqW30ceXRfKMNaYhI68vriyVdybtMtTiZa8="
DEVICE_ID = "rpi"

CONNECTION_STR = "HostName=programming-arduino.azure-devices.net;DeviceId=rpi;SharedAccessKey=hZiVwRZTYig5xWgVr6vGVUgfzOyctlOSq1McMcaWY04="
iothub_registry_manager = IoTHubRegistryManager(IOTHUB_CONNECTION_STRING)
twin2 = iothub_registry_manager.get_twin(DEVICE_ID)

codes_start = 0

class LineUs:
    """An example class to show how to use the Line-us API"""

    def __init__(self, line_us_name):
        self.__line_us = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__line_us.connect((line_us_name, 1337))
        self.__connected = True
        self.__hello_message = self.__read_response()

    def get_hello_string(self):
        if self.__connected:
            return self.__hello_message.decode()
        else:
            return 'Not connected'

    def disconnect(self):
        """Close the connection to the Line-us"""
        self.__line_us.close()
        self.__connected = False

    def goTo(self, x, y, z):
        """Send a G01 (interpolated move), and wait for the response before returning"""
        cmd = b'G01 X'
        cmd += str(x).encode()
        cmd += b' Y'
        cmd += str(y).encode()
        cmd += b' Z'
        cmd += str(z).encode()
        self.__send_command(cmd)
        self.__read_response()

    def __read_response(self):
        """Read from the socket one byte at a time until we get a null"""
        line = b''
        while True:
            char = self.__line_us.recv(1)
            if char != b'\x00':
                line += char
            elif char == b'\x00':
                break
        return line

    def __send_command(self, command):
        """Send the command to Line-us"""
        command += b'\x00'
        self.__line_us.send(command)

#my_line_us = LineUs('line-us.local')


def handle_twin(twin):
    codes_start = int(time.time()) 
    #print("Twin received", twin)
    if ('desired' in twin):
        desired = twin['desired']
        #print(desired['code'])
        code = str(desired['code'])
       
        #Create a new executable file
        if (desired['updated']==1):
            print('code is updated')
            fin = open("setup.c", "rt")
            #output file to write the result to
            name = "test{}".format(codes_start)
            nfout = "{}.c".format(name)
            sofout = "{}.so".format(name)
            fout = open(nfout, "wt")
            print(nfout, 'name of code')
            #for each line in the input file
            for line in fin:
                #read replace the string and write to output file
                fout.write(line)
            fout.write(code)
            fout.write("shutdown(sockfd, SHUT_RDWR);}")
            #close input and output files
            fout.close()
            fin.close()
            print("files are written")
            time.sleep(0.3)
            #make the binding to the so file
            try:
                bashCommand = "cc -fPIC -shared -o {} {}".format(sofout,nfout)
                import subprocess
                subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            except:
                print('failed making binding')
            time.sleep(0.3)
            print('so is bounded')
            #call uploaded code
            from ctypes import CDLL
            so_file = "/home/pi/remotelab/{}".format(sofout)
            try:
                my_functions = CDLL(so_file)
                my_functions.main()
                del my_functions
                print('code is executed')
            except:
                print('code could not be executed')
            #codes_start = codes_start + 1
            twin_patch = Twin(properties= TwinProperties(desired={'updated' : 0}))
            iothub_registry_manager.update_twin(DEVICE_ID, twin_patch, twin2.etag)
            #os.execl(sys.executable, sys.executable, *sys.argv)
            

async def main():

    conn_str = CONNECTION_STR
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await device_client.connect()

	#twin.Properties.Desired["led"] = led_val;
        

    while True:
        twin = await device_client.get_twin()
        handle_twin(twin)

        time.sleep(1)

    await device_client.disconnect()



if __name__ == "__main__":
    asyncio.run(main())
