import threading
import socket
import json
import termcolor
import time
import numpy as np
import pandas as pd

USER = '' # Username will be enterd by User
PASS = '' # Password Will be input bu user
is_auth = False # is user authorized ro neter into chat?
USERS = [] # users available for chat will be fetch from server
CHATTING_WITH = '' # User Selected for chat
is_selected = False # boolean is user selected for chat

SERVER_IP   = '127.0.0.1'
SERVER_PORT = 9999

#Create a new socket using the given address family, socket type and protocol number. 
#ipv4 family
#TCP (SOCK_STREAM) is a connection-based protocol. The connection is established 
#and the two parties have a conversation until the connection is terminated by one of the parties or by a network error.
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT)) # connectting with serverip and port

def authenticator():
    '''
        Function to get inputs from users like username and password.
        Communicates with server.
        Sends Credentials to Server and If authorized by server, returns True.

    '''
    global USER
    global PASS
    global USERS
    isConn=False
    #iterate until not authroized
    while not isConn:
        USER = validate_striing('Enter username:')
        PASS = validate_striing('Enter password:')
        reliable_send(['auth',USER,PASS])
        time.sleep(0.050)
        data = reliable_recv()
        time.sleep(0.050)
        #check response from server
        if data[0]=='auth_res':
            #will set true if authorized
            isConn=data[1]
            #get users from db for chat 
            USERS=list(data[2])
            if isConn:
                print(termcolor.colored('[+] You are authenticated ...', 'green'))
            else:
                print(termcolor.colored('[+] You have entered an invalid username or password!', 'red'))
    return isConn

def select_user_for_chat():
    '''
    Asks user for for serial of users, displayed, available for chat.
    Selected user assigned to CHATTING with variable.
    Return True on selection.
    '''
    global USERS
    global CHATTING_WITH
    isSelected=False
    #iterate until not selected
    while not isSelected:
        #printing users with index
        for i,name in enumerate(USERS):
            print('{} >> {}\n'.format(i,name) )
        #get serial from user
        num=get_number('Enter username serial number from above to chat:')
        #update chatting with varibale
        CHATTING_WITH=USERS[num]
        #on selection display you are chatting with
        if len(str(CHATTING_WITH)):
            print(termcolor.colored('[+] You are now chatting with '+str(CHATTING_WITH)))
            isSelected=True
        else:
            print(termcolor.colored('[+] You have selected an invalid username', 'red'))
    return isSelected

def get_number(string):
    '''
    Helps get digit input from user and keeps asking on wrong entry.
    '''
    number=input(string)
    if not number.isdigit():
        validate_striing('Enter a number!' + string)        
    return int(float(number))

def client_receive():
    '''
    Receive function for client, will work in a thread and checks are ended:
     1. When to end chat
     2. Sending alias or username to server
     3. checking received message for authorized client for chat (message sender and receiver)
      and displaying them.
    '''
    global USER
    global CHATTING_WITH
    global is_selected
    while True:
        try:
            message = reliable_recv()
            #check if server asks for username
            if message == 'alias?':
                reliable_send(USER)
            #check for end command
            elif str(message[1])== CHATTING_WITH and str(message[2])==USER and str(message[3])=='@end' :
                is_selected=False
                CHATTING_WITH=''
            #check if message is from authorized client
            elif str(message[1])== CHATTING_WITH and str(message[2])==USER :
                print('{} > {}'.format(message[1],message[3]))
            else:
                continue
        except:
            print('Error!')
            client.close()
            break

def client_send():
    '''
    Send function for client, will work in a separate thread and checks are ended:
        1. Asking User for person to chat with by calling select_user_for_chat function
        2. checking message to be send, command @end, to end chat timely.
        3. message send formatted as [sender,receiver, message] list
    '''
    global CHATTING_WITH
    global is_selected
    while True:
        if not CHATTING_WITH and not is_selected:
            is_selected = select_user_for_chat()
        elif is_selected==True:
            input_msg=input('')
            if input_msg.lower()=='@end':
                # check for chat end command
                reliable_send(['messaging',USER,CHATTING_WITH,input_msg])
                is_selected=False
                CHATTING_WITH=''
            else:
                #sending formatted message
                reliable_send(['messaging',USER,CHATTING_WITH,input_msg])

def reliable_send(data):
    '''
    Reliable send, json object encoded as string

    '''
    #json.dumps() takes in a json object and returns a string.

    jsondata = json.dumps(data)
    client.send(jsondata.encode())

def reliable_recv():
    '''
    Receive as long as there is something to receive, can receive more than 1024 bytes
    '''
    
    data = ''
    while True:
        try:
            #receive as long as there is something to receive
            data = data + client.recv(1024).decode().rstrip()
            #json.loads() takes in a string and returns a json object.
            return json.loads(data)
        except ValueError:
            continue

def validate_striing(string):
    
    '''
    To get string from user and check if its or not 
    if it is then ask again
    '''
    name = input(string)
    if not len(str(name)):
        #if empty ask again
        validate_striing('Empty!' + string)        
    return name

def initialize():
    '''
    check users entered details for auth from client, received by calling authenticator function.
    Once user auth remove user alias from users list and initiate multithreads of receiving and sending.
    '''
    print(termcolor.colored('[+] Connected to the Server ...', 'green'))

    global is_auth
    global USER
    while not is_auth:
        is_auth = authenticator()
        print('is_auth', is_auth)
        if is_auth:    
            USERS.remove(USER)
            receive_thread = threading.Thread(target=client_receive)
            receive_thread.start()

            send_thread = threading.Thread(target=client_send)
            send_thread.start()
    
def main():
    initialize()

#starting program
if __name__ == '__main__': main()