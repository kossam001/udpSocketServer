import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
      else:
         if 'connect' in data:
            # Fill in client information and add to dict
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0

            # Initialize message to be sent to new player
            GameState = {"cmd": 1, "players": []}

            # C# Command class, Player class
            message = {"cmd": 0,"player":{"id":str(addr)}} #0 = new player connected
            m = json.dumps(message)
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1])) #0 = address, 1 = port
               # Create information about the other clients
               player = {}
               player['id'] = str(c) # (address, port)
               # Add information to message
               GameState['players'].append(player)

            # Send the new player the clients list
            new_client_m = json.dumps(GameState)
            sock.sendto(bytes(new_client_m, 'utf8'), addr)

def cleanClients(sock):
   while True:
      dropped_players = []
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:

            # Track dropped player
            player = {}
            player['id'] = str(c)
            dropped_players.append(player)

            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()

      # Message all connected clients about dropped clients
      if (len(dropped_players) > 0):
         message = {"cmd": 2, "players": dropped_players}
         m = json.dumps(message);
         for c in clients:
            sock.sendto(bytes(m, 'utf8'), (c[0], c[1]))
      
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
