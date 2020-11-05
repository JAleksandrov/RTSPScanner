import subprocess
import socket
import shlex
import threading
import time
import requests
import RPi.GPIO as GPIO
from PIL import Image
from io import BytesIO

################### This is the main class ##########
####### It sets the GPIO that will be used ##########
###### Green LED for scanning will be connected at GPIO 11 ########
###### Red LED at GPIO 7 will light up if no ethernet port is connected #########
class MainClass:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        GPIO.setup(7,GPIO.OUT)          #Red Led
        GPIO.setup(11,GPIO.OUT)         #Green Led
        GPIO.output(7,GPIO.LOW)
        GPIO.output(11,GPIO.LOW)
        

        self.out = subprocess.Popen(['ethtool','eth0'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        
        self.stdout,self.stderr = self.out.communicate()
        
        
        ########### This function checks if the ethernet is connected or not##########
        ##########  return True if connected and false if not and glows red led ########
    def Check_ConnectionStatus(self):
        if "Link detected: no" in self.stdout.decode('utf-8'):
            GPIO.output(7,GPIO.HIGH)
            return False
        elif "Link detected: yes" in self.stdout.decode('utf-8'):
            GPIO.output(7,GPIO.LOW)
            return True
        
######################### This class is used to get data from API        
class get_set_Values:
    
    ###### This function get raspberry pi info   ########
    def get_Values_from_Table_Raspberries(self):
        self.response_Rpi = requests.get("{get data from raspi user}")
        if self.response_Rpi.status_code!=200:
            print("unable to connect to API")
        else:
            self.Complete_RPI_Info = self.response_Rpi.json()
            self.RPI_Data = self.Complete_RPI_Info["data"]
            self.RPI_Info_Dict = {
                "username" : self.RPI_Data[0]["username"],
                "password" : self.RPI_Data[0]["password"],
                "raspi_id" : self.RPI_Data[0]["raspi_id"],
                "function" : self.RPI_Data[0]["function"]
                }
        return(self.RPI_Info_Dict)
    
    ######## this function gets list of URL from API ##########
    def get_URL_List(self):
        self.response_url = requests.get("{Get rtsp urls}")
        if self.response_url.status_code!=200:
            print("unable to connect to API")
        else:
            self.url_List = []
            self.All_URL_API_Data = self.response_url.json()
            self.All_URL = self.All_URL_API_Data["data"]
            for url in self.All_URL:
                self.url_List.append(url["url"])
            return(self.url_List)
        
    def post_Url(self,url_toPost_List):
        self.url_toPost_List = url_toPost_List
        self.List_for_post = []
        for i in range (1,len(self.url_toPost_List)+1):
            empty_dict = { }
            empty_dict["id"] = str(i)
            empty_dict["url"] = str(self.url_toPost_List[i-1])
            self.List_for_post.append(empty_dict)
        self.final_dict = {}
        self.final_dict["url_data"] = self.List_for_post
        self.url_to_add = "{url_to_dvr}"
        self.info = json.dumps(self.final_dict)
        self.request_json = json.loads(self.info)
        requests.post(self.url_to_add,self.request_json)

        

class handle_Functions:
    def __init__(self):
        self.updated_url_List = []
        self.url_List_with_Img = []
        
    def update_URL(self,url,Extracted_RPI_Info_Dict):
        self.url = url
        self.Extracted_RPI_Info_Dict = Extracted_RPI_Info_Dict
        if "[CHANNEL]" not in self.url:
            self.updated_username = self.url.replace("[USERNAME]",self.Extracted_RPI_Info_Dict["username"])
            self.updated_password = self.updated_username.replace("[PASSWORD]",self.Extracted_RPI_Info_Dict["password"])
            
            self.updated_url_List.append("https://" + ip + self.updated_password)
        elif "[CHANNEL]" in self.url:
            self.updated_username = self.url.replace("[USERNAME]",self.Extracted_RPI_Info_Dict["username"])
            self.updated_password = self.updated_username.replace("[PASSWORD]",self.Extracted_RPI_Info_Dict["password"])
            for i in range (1,9):
                self.updated_url = "https://" + ip + self.updated_password.replace("[CHANNEL]",str(i))
                self.updated_url_List.append(self.updated_url)
                
    def check_URl_have_Image(self,url_List_to_check_image):
        self.url_List_to_check_image = url_List_to_check_image
        for image_check in self.url_List_to_check_image:
            response = requests.get(image_check)
            try:
                img = Image.open(BytesIO(response.content))
                self.url_List_with_Img.append(image_check)
            except:
                print("image not found")
                pass
        return(self.url_List_with_Img)
            
    def get_Updated_URL(self):
        return (self.updated_url_List)
        
    def func2(self):
        print("Funcion 2 executed")
        
    def func3(self):
        print("Function 3 executed")
    
##### this class does the network scanning and runs a seperate thread for it ########
class run_NetworkScan:
    def __init__(self):
        self.isScanning = False
        self.active_IP_List = []
        self.active_IP_Port_List = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.thread = threading.Thread(target=self.start_Scan)
        
    def start_Scan(self):
        del self.active_IP_List[:]
        del self.active_IP_Port_List[:]
        self.isScanning = True
        for i in range (1,254):
            pingStr = "ping -c1 192.168.10." + str(i)    ####### Network ip can be edited here, edit as per your network id
            cmd = shlex.split(pingStr)
            try:
                output_pingState = subprocess.check_output(cmd)
            except:
                pass
            else:
                self.active_IP_List.append(str(cmd[-1]))
                
        for ip in self.active_IP_List:
            try:
                a= self.sock.bind((ip,2535))
                self.active_IP_Port_List.append(ip)
            except:
                print(ip,"this ip port is in use")
                pass
        self.isScanning = False
        
        ###### This fucntion returns the scanning status that is network scanning is going on?####
    def scanning_Status(self):
        return self.isScanning
    
    ####### this function returns the list of active ip with port 80 available#######
    def get_available_IP_with_Port80(self):
        return self.active_IP_Port_List
        
    ###### this function starts the scanning thread #########
    def initialize_Scanner(self):
        self.thread.start()

            

checkConnection = MainClass()
GetSetValues = get_set_Values()
networkScanner = run_NetworkScan()
handleFunctions = handle_Functions()

status = checkConnection.Check_ConnectionStatus()

if status==False:
    print("Stop ethernet not connected")
    
elif status==True:
    Extracted_RPI_Info_Dict = GetSetValues.get_Values_from_Table_Raspberries()
    if Extracted_RPI_Info_Dict["function"]=='1':
        networkScanner.initialize_Scanner()
        while True:
            isScanning = networkScanner.scanning_Status()
            if isScanning == False:
                GPIO.output(11,GPIO.LOW)
                break
            elif isScanning == True:
                GPIO.output(11,GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(11,GPIO.LOW)
            
        for ip in networkScanner.get_available_IP_with_Port80():
            for url in GetSetValues.get_URL_List():
                handleFunctions.update_URL(url,Extracted_RPI_Info_Dict)
                
            
        List_of_Url_with_Image = handleFunctions.check_URl_have_Image(handleFunctions.get_Updated_URL())
        GetSetValues.post_Url(List_of_Url_with_Image)
                

    
