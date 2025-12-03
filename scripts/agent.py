__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *

from threading import Thread
import numpy as np
from time import sleep


class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):
        #TODO: DEINE YOUR ATTRIBUTES HERE

        #DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]   #initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]   #environment dimensions
        cell_val = env_conf["cell_val"] #value of the cell the agent is located in
        #ADD : 
        self.path = [(self.x, self.y)]
        print(cell_val)
        Thread(target=self.msg_cb, daemon=True).start()
        print("hello")
        self.wait_for_connected_agent()

        
    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            self.msg = msg
            if msg["header"] == MOVE:
                self.x, self.y =  msg["x"], msg["y"]
                print(self.x, self.y)
            elif msg["header"] == GET_NB_AGENTS:
                self.nb_agent_expected = msg["nb_agents"]
            elif msg["header"] == GET_NB_CONNECTED_AGENTS:
                self.nb_agent_connected = msg["nb_connected_agents"]

            print("hellooo: ", msg)
            print("agent_id ", self.agent_id)
            

    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("both connected!")
                check_conn_agent = False

    #TODO: CREATE YOUR METHODS HERE...

    #added : 
    def map_division(self):
        """ Method used to divide the map among agents """
        if self.nb_agent_expected == 2: 
            y = self.w // 2
            x = self.h
        elif self.nb_agent_expected == 3:
            y = self.w // 3
            x = self.h
        elif self.nb_agent_expected == 4:
            y = self.w // 2
            x = self.h // 2
        return x, y  
    
    def choose_map_division(self):
        x,y = self.map_division(self)
        if self.nb_agent_expected == 2:
            if self.agent_id == 0:
                limit_x = (0, x)
                limit_y = (0, self.h)
            else:
                limit_x = (x, self.w)
                limit_y = (0, self.h)
        elif self.nb_agent_expected == 3:
            if self.agent_id == 0:
                limit_x = (0, x)
                limit_y = (0, self.h)
            elif self.agent_id == 1:
                limit_x = (x, 2*x)
                limit_y = (0, self.h)
            else:
                limit_x = (2*x, self.w)
                limit_y = (0, self.h)
        elif self.nb_agent_expected == 4:
            if self.agent_id == 0:
                limit_x = (0, x)
                limit_y = (0, y)
            elif self.agent_id == 1:
                limit_x = (x, self.w)
                limit_y = (0, y)
            elif self.agent_id == 2:
                limit_x = (0, x)
                limit_y = (y, self.h)
            else:
                limit_x = (x, self.w)
                limit_y = (y, self.h)
        return limit_x, limit_y


    def move_agent(self):
        """ Method used to move the agent in the environment """
        x = self.x
        y = self.y
        movement = randint(1,8)
        moves = {
            1: (-1, 0),  # LEFT
            2: (1, 0),   # RIGHT
            3: (0, -1),  # UP
            4: (0, 1),   # DOWN
            5: (-1, -1), # UP-LEFT
            6: (1, -1),  # UP-RIGHT
            7: (-1, 1),  # DOWN-LEFT
            8: (1, 1),   # DOWN-RIGHT
        }
        dx, dy = moves.get(movement, (0,0))
        x = self.x + dx
        y = self.y + dy
        
        #test des voisins pr check qu'il y a des dispo
        neighbors = []
        for ddx, ddy in moves.values():
            nx, ny = self.x + ddx, self.y + ddy
            if 0 <= nx < self.w and 0 <= ny < self.h:
                neighbors.append((nx, ny))

        #si il est entourer de voisins dans le path
        blocked = len(neighbors) > 0 and all(n in self.path for n in neighbors)
        print("blocked: ", blocked)

        if x < limit_x1 or x >= limit_x2 or y < limit_y1 or y >= limit_y2 and (x, y) != ((limit_x1,limit_y1) or (limit_x2-1, limit_y2-1) or (limit_x1, limit_y2-1) or (limit_x2-1, limit_y1)):
            print("je suis dans les limites avec ", x, y)
            movement = 0   #STAND
            print("movement: ", movement, "my position: ", self.x, self.y)
        elif (x, y) in self.path and not blocked :
            movement = 0   #STAND
            print("je suis dans le path ", x, y)
            print("movement: ", movement, "my position: ", self.x, self.y)
        else:
            self.network.send({"header": MOVE, "direction": movement})
            print("movement: ", movement, "my position: ", self.x, self.y)
        self.path.append((self.x, self.y))
        sleep(0.2)

        def box_key_pattern(self):
            
  
            return 0
                 

            
 
if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    try : 
        limit_x, limit_y = agent.choose_map_division()
        limit_x1 = limit_x[0]
        limit_x2 = limit_x[1]
        limit_y1 = limit_y[0]
        limit_y2 = limit_y[1]
        while True: 
            agent.move_agent(limit_x1, limit_x2, limit_y1, limit_y2)
        try:    #Manual control test0
            while True:
                cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
                if cmds["header"] == BROADCAST_MSG:
                    cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                    cmds["position"] = (agent.x, agent.y)
                    cmds["owner"] = randint(0,3) # TODO: specify the owner of the item
                elif cmds["header"] == MOVE:
                    cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
                agent.network.send(cmds)
        except KeyboardInterrupt:
            pass
    except KeyboardInterrupt:
        pass

# it is always the same location of the agent first location