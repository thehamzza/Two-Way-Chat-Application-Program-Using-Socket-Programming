import threading
import socket
import json
import termcolor
import time
import numpy as np
import pandas as pd

IP      = '127.0.0.1'   # server ip
# IP      = socket.gethostname()      # server ip
PORT    = 9999                      # server port
ADDRESS = IP, PORT

# Create a new socket using the given address family, socket type and protocol number. 
# ipv4 family
# TCP (SOCK_STREAM) is a connection-based protocol. The connection is established 
# and the two parties have a conversation until the connection is terminated by one of the parties or by a network error.

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Allows a socket to bind to an address and port already in use.

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDRESS) # binidng port ip with server
server.listen() 
clients = []
aliases = []



def specific_send(message):
    '''
    This function forwards messages to respective clients after checking the authenticity
    '''
    receiver    = message[2] # read message list 0 index
    index       = aliases.index(receiver)
    client      = clients[index]

    send_to_socket(client,message)

# Function to handle clients'connections
def get_users():
    '''
    Read username column from db and return
    '''
    df  =   pd.read_csv('users.csv')
    new =   df['username'].to_numpy().tolist()
    return new

def recv_all(target):
    '''
    Receive as long as there is something to receive,
    can receive more than 1024 bytes
    '''
    data = ''
    while True:
        try:
            # rstrip removes spaces at end
            data = data + target.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

def send_to_socket(target, data):
    '''
    Reliable send, json object encoded as string

    '''
    # json.dumps() takes in a json object and returns a string.

    jsondata = json.dumps(data)
    target.send(jsondata.encode())

def handle_client(client):
    '''
    Works in different thread,
    handle every client connects with server
    checks header to call specific function
    '''
    while True:
        try:
            message = recv_all(client)
            if str(message[0])=='messaging':
                # messageing meant between specific clients
                specific_send(message)
            else:
                # if not broadcast
                broadcast(message)
    
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            alias = aliases[index]
            aliases.remove(alias)
            #remove client if disconnected from list
            break
# Main function to receive the clients connection

def authenticate_user(name,password):
    '''
    Loading users from db and comparing with fed name and password
    and returns true if authenticated
    '''
    #checks for password and username parameters
    df=pd.read_csv('./users.csv')
    row=df.loc[df['username']==name]
    isAuth=False
    row=np.array(row)
    if row.size:
        isAuth=row[0][1]==password
    return isAuth

def broadcast(message):
    '''
    Broadcast messages ato all clients
    '''
    for client in clients:
        send_to_socket(client,message)

def receive():
    '''
    Once User connects it, checks user credentials with db and send auth=true Response to clients, then client get authenticated.
    It also asks for clients name and then calls sender and receiver threads.
    '''
    while True:
        print(termcolor.colored(f'[+] Server is Running on address {ADDRESS} \n    Waiting for incoming connections ...', 'green'))
        client, address = server.accept()
        isAuth = False
        while not isAuth:
            data = recv_all(client)
            time.sleep(0.05)
            if data[0] == 'auth':
                isAuth = authenticate_user(data[1],data[2])
                users_list = get_users()
                time.sleep(0.050)
                send_to_socket(client, ['auth_res', isAuth, users_list]) 
                time.sleep(0.050)
        
        time.sleep(2)
        # print(termcolor.colored(str(address) + ' has connected!', 'green'))
        send_to_socket(client,'alias?')
        alias = recv_all(client)
        aliases.append(alias)
        clients.append(client)
        print(f'[{ address[0] }: { address[1] }] joined in as {alias}')
        send_to_socket(client,'you are now connected!')
        thread = threading.Thread(target= handle_client, args= (client,))
        thread.start()

def main():
    receive()

if __name__ == '__main__': main()