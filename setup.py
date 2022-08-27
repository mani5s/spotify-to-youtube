import os
import time
from os.path import exists

def setup():
    if not exists("installed.txt"):
        print("Installing requires libraries")
        time.sleep(1)
        os.system("pip install -r requirements")
        os.system("echo LIBRARIES EXIST! > installed.txt")
        print("Libraries installed")
        print("CLEARING command prompt to start setup process")
        os.system("cls")
        

    print("""Please enure you have the following materials ready for your setup process
    1)Spotify CLient ID
    2)Spotify Client Secret
    3)Youtube API key
    4)Youtube client id
    5)Youtube client secret
    if you do not have any of the items above, please refer to the 'README' to obtain these details""")
    ready = input("Do you have the information available to you? 'yes/no'  ").lower()
    if ready != "yes":
        print("Please re-run this program after getting the information")
        time.sleep(2)
        return False