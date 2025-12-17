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

        self.move_to_str = {
            (-1, 0): LEFT,  # LEFT
            (1, 0): RIGHT,   # RIGHT
            (0, -1): UP,  # UP
            (0, 1): DOWN,   # DOWN
            (-1, -1): UP_LEFT, # UP-LEFT
            (1, -1): UP_RIGHT,  # UP-RIGHT
            (-1, 1): DOWN_LEFT,  # DOWN-LEFT
            (1, 1): DOWN_RIGHT,   # DOWN-RIGHT
        }

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
        self.cell_val = cell_val
        #ADD : 
        self.path = [(self.x, self.y)]
        self.cell_val = float(cell_val) 
        self.path = [(self.x, self.y)]
        self.last_move = 0

        # basic memories for discovered items
        self.detected_items = []
        self.KEYS_coordonates = []
        self.BOXES_coordonates = []
        self.foreign_items = set()  
        self.positions = set() 
        self.my_key_found = False  
        self.my_box_found = False

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
                #print(self.x, self.y)
            elif msg["header"] == GET_NB_AGENTS:
                self.nb_agent_expected = msg["nb_agents"]
            elif msg["header"] == GET_NB_CONNECTED_AGENTS:
                self.nb_agent_connected = msg["nb_connected_agents"]

            if "cell_val" in msg:
                self.cell_val = msg["cell_val"]

            #print("hellooo: ", msg)
            #print("agent_id ", self.agent_id)
            

    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("both connected!")
                check_conn_agent = False

    #TODO: CREATE YOUR METHODS HERE...

    #added : 
    #Partie de martin
    def agent_management(self):
        """
        Stop Agent's observation when all items are detected and registered, and start a_start to reach keys and boxes
        """
        sleep(1)
        self.total_objects = self.nb_agent_expected * 2
        #print(len(self.detected_items), " items detected so far.")
        #print(self.total_objects, " items to be detected in total.")
           
        # continue exploration until all items have been found
        while len(self.detected_items) < self.total_objects:

            # agent continue to move
            self.move_agent()
            
            # Request item owner info
            self.network.send({"header": GET_ITEM_OWNER})

            # Get item owner response
            item_response = self.wait_for_response(GET_ITEM_OWNER)
            owner = item_response.get("owner")
            item_type = item_response.get("type")

            # If agent is on an item 
            if owner is not None and item_type is not None:
                print("I'm here - 3")
                # Get current item coordinates
                item_coords = (self.x, self.y)
                
                # Check if item already registered
                already_registered = any(item[0] == item_coords[0] and item[1] == item_coords[1] for item in self.detected_items)
                
                if not already_registered:
                    # rgister the item
                    self.detected_items.append((item_coords[0], item_coords[1], owner, item_type))
                    
                    # Store in list for each type of item
                    if item_type == KEY_TYPE:
                        self.KEYS_coordonates.append((item_coords, owner))
                        print(f"KEY discovered at {item_coords}, owner: {owner}")

                    elif item_type == BOX_TYPE:
                        self.BOXES_coordonates.append((item_coords, owner))
                        print(f"BOX discovered at {item_coords}, owner: {owner}")
            else:
                continue  # No item found, continue exploration
        
        # All items have been found => exploration is completed
        # print("All items have been found => exploration phase complete")
        # print(f"Keys found: {self.KEYS_coordonates}")
        # print(f"Boxes found: {self.BOXES_coordonates}")
        
        # NOW Implement A* algorithm to:
        # 1. Go to key
        # 2. Go to box

    def map_division(self): #Fonctionnel
        """ Method used to divide the map among agents """
        x = self.w
        y = self.h
        if self.nb_agent_expected == 2: 
            y = self.h 
            x = self.w //2
        elif self.nb_agent_expected == 3:
            y = self.h 
            x = self.w //3
        elif self.nb_agent_expected == 4:
            y = self.h // 2
            x = self.w // 2
        return x, y  
    
    def choose_map_division(self): #Fonctionnel
        x,y = self.map_division()
        limit_x = (0, self.w)
        limit_y = (0, self.h)
        if self.nb_agent_expected == 2:
            if self.agent_id == 0:
                limit_x = (0, x)
                limit_y = (0, y)
            else:
                limit_x = (x, x*2)
                limit_y = (0, y)
        elif self.nb_agent_expected == 3:
            if self.agent_id == 0:
                limit_x = (0, x)
                limit_y = (0, y)
            elif self.agent_id == 1:
                limit_x = (x, x*2)
                limit_y = (0, y)
            else:
                limit_x = (x*2, x*3)
                limit_y = (0, y)
        elif self.nb_agent_expected == 4:
            if self.agent_id == 0:
                limit_x = (0, x)
                limit_y = (0, y)
            elif self.agent_id == 1:
                limit_x = (x, x*2)
                limit_y = (0, y)
            elif self.agent_id == 2:
                limit_x = (0, x)
                limit_y = (y, y*2)
            else:
                limit_x = (x, x*2)
                limit_y = (y, y*2)
        return limit_x, limit_y

    def move_diagonal(self, limit_x1, limit_x2, limit_y1, limit_y2):
        x = self.x
        y = self.y
        print("my position" , self.x, self.y)
        print("last posi" , self.path[-1])
        print("next posi" , x,y-1)
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
        #Check si on est sur l'angle en haut à gauche
        if x + 1 > limit_x2 and y - 1 > limit_y1 :

            movement = 7  #DOWN-LEFT
            self.last_move = movement
            self.network.send({"header": MOVE, "direction": movement})
            sleep(0.5)
            self.path.append((self.x, self.y))
       
        elif self.cell_val == 0.25 or self.cell_val == 0.3:
            # if case already discovered
            if self.avoid_pattern():
                print(f"PATTERN IGNORED")
                movement = self.last_move
                self.network.send({"header": MOVE, "direction": movement})
                sleep(0.5)
                self.path.append((self.x, self.y))
                
                
                # if closed to box
            elif self.cell_val == 0.3:
                #print("je suis proche d'une box")
                self.search_box_around(moves,limit_x1, limit_x2, limit_y1, limit_y2)
                self.path.append((self.x, self.y))
                sleep(0.2)
                

                #if closed to key
            elif self.cell_val == 0.25:
                #print("je suis proche d'une key")
                self.search_key_around(moves,limit_x1, limit_x2, limit_y1, limit_y2)
                self.path.append((self.x, self.y))
                sleep(0.2)
                
            
        elif x -1 < limit_x1 and (x,y-1) not in self.path:
            i = 0
            for i in range(0,4):
                print("i :" , i)
                movement = 3  #UP
                self.last_move = movement
                self.network.send({"header": MOVE, "direction": movement})
                sleep(0.5)
                i += 1
                self.path.append((self.x, self.y))
            movement = 6 #UP-LEFT
            self.last_move = movement
            self.network.send({"header": MOVE, "direction": movement})
            sleep(0.5)
            self.path.append((self.x, self.y))
        elif y -1 < limit_y1 and x+1 <= limit_x2 and (x-1,y) not in self.path:
            i = 0
            for i in range(0,4):
                print("i :" , i)
                movement = 1  #LEFT
                self.last_move = movement 
                self.network.send({"header": MOVE, "direction": movement})
                sleep(0.5)
                i += 1
                self.path.append((self.x, self.y))
            movement = 7  #DOWN-LEFT
            self.last_move= movement
            self.network.send({"header": MOVE, "direction": movement})
            sleep(0.5)
            self.path.append((self.x, self.y))
        elif y+1 >= limit_y2 and (x-1,y) not in self.path:
            i = 0
            for i in range(0,4):
                print("i :" , i)
                movement = 1  #LEFT
                self.last_move = movement
                self.network.send({"header": MOVE, "direction": movement})
                sleep(0.5)
                i += 1
                self.path.append((self.x, self.y))
            movement = 6  #UP-LEFT
            self.last_move = movement
            self.network.send({"header": MOVE, "direction": movement})
            sleep(0.5)
            self.path.append((self.x, self.y))
        elif x >= limit_x2-1 :
            i = 0
            for i in range(0,4):
                print("i :" , i)
                movement = 3  #UP
                self.last_move = movement
                self.network.send({"header": MOVE, "direction": movement})
                sleep(0.5)
                i += 1
                self.path.append((self.x, self.y))
            movement = 7  #DOWN-LEFT
            self.last_move = movement
            self.network.send({"header": MOVE, "direction": movement})
            sleep(0.5)
            self.path.append((self.x, self.y))
            
        elif y -1 > limit_y1 - 1 and (x-1,y+1) in self.path:
            movement = 6 #UP-LEFT
            self.last_move = movement
            self.network.send({"header": MOVE, "direction": movement})
            sleep(0.5)
            self.path.append((self.x, self.y))
        else : 
            movement = 7  #DOWN-LEFT
            self.last_move = movement
            self.network.send({"header": MOVE, "direction": movement})
            sleep(0.5)
            self.path.append((self.x, self.y))

    def move_agent(self,limit_x1, limit_x2, limit_y1, limit_y2):
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
        print("cell_val", self.cell_val)
        neighbors = []
        for ddx, ddy in moves.values():
            nx, ny = self.x + ddx, self.y + ddy
            if limit_x1 <= nx < limit_x2 and limit_y1 <= ny < limit_y2:
                neighbors.append((nx, ny))

        #si il est entourer de voisins dans le path
        blocked = len(neighbors) > 0 and all(n in self.path for n in neighbors)

        if self.cell_val == 0.25 or self.cell_val == 0.3:
            # if case already discovered
            if self.avoid_pattern():
                print(f"PATTERN IGNORED")
                
                # if closed to box
            elif self.cell_val == 0.3:
                #print("je suis proche d'une box")
                self.search_box_around(moves,limit_x1, limit_x2, limit_y1, limit_y2)
                self.path.append((self.x, self.y))
                sleep(0.2)
                return

                #if closed to key
            elif self.cell_val == 0.25:
                #print("je suis proche d'une key")
                self.search_key_around(moves,limit_x1, limit_x2, limit_y1, limit_y2)
                self.path.append((self.x, self.y))
                sleep(0.2)
                return

        if x < limit_x1 or x >= limit_x2 or y < limit_y1 or y >= limit_y2 and (x, y) != ((limit_x1,limit_y1) or (limit_x2-1, limit_y2-1) or (limit_x1, limit_y2-1) or (limit_x2-1, limit_y1)):
            #print("je suis dans les limites avec ", x, y)
            movement = 0   #STAND
            #print("movement: ", movement, "my position: ", self.x, self.y)
        elif (x, y) in self.path and not blocked :
            movement = 0   #STAND
            #print("je suis dans le path ", x, y)
            #print("movement: ", movement, "my position: ", self.x, self.y)


        else:
            self.network.send({"header": MOVE, "direction": movement})
            #print("movement: ", movement, "my position: ", self.x, self.y)
        self.path.append((self.x, self.y))
        sleep(0.2)


    def request_item_owner(self):
        """Demande synchrone au jeu quel est l'item sous le robot."""
        self.network.send({"header": GET_ITEM_OWNER})
        # on attend la réponse correspondante de façon simple
        while True:
            msg = self.msg
            if msg.get("header") == GET_ITEM_OWNER:
                return msg
            sleep(0.05)


    def search_box_around(self,moves,limit_x1, limit_x2, limit_y1, limit_y2):
        """Teste les 8 cases autour"""
        directions = [3, 2, 4, 4, 1, 1, 3, 3]

        for d in directions:

            dx, dy = moves.get(d, (0,0))

            x = self.x + dx
            y = self.y + dy

            if limit_x1 <= x < limit_x2 and limit_y1 <= y < limit_y2:

                self.network.send({"header": MOVE, "direction": d})
                sleep(0.2)
            
            else :
                print("LIMIT")
                self.network.send({"header": MOVE, "direction": 0})


            if self.cell_val == BOX_NEIGHBOUR_PERCENTAGE:
                #print("cell_value", self.cell_val)
                directions = [3, 2, 4, 4, 1, 1, 3, 3]

                for i in directions:
                    dx, dy = moves.get(i, (0,0))

                    x = self.x + dx
                    y = self.y + dy
                    if limit_x1 <= x < limit_x2 and limit_y1 <= y < limit_y2:
                        print("LIMIT")
                        self.network.send({"header": MOVE, "direction": i})
                        print(f"i : {i} cell value : {self.cell_val}")
                        sleep(0.2)
                
                    else :
                        self.network.send({"header": MOVE, "direction": 0})

            
                    if self.cell_val == 1.0:
                        info = self.request_item_owner()
                        owner = info.get("owner")
                        item_type = info.get("type")
                        
                        if item_type == BOX_TYPE:
                            if owner is not None and owner != self.agent_id:
                                # Item étranger - ajouter aux foreign items
                                self.foreign_items.add((self.x, self.y, owner, BOX_TYPE))
                                self.positions.add((self.x, self.y))
                                print(f"not my box on ({self.x}, {self.y}), owner: {owner}")
                                
                                for dx in [-1, 0, 1]:
                                    for dy in [-1, 0, 1]:
                                        neighbor = (self.x + dx, self.y + dy)
                                        if neighbor not in self.path:
                                            self.path.append(neighbor)
                                
                            else:
                                self.my_box_found = True
                                self.BOXES_coordonates.append(((self.x, self.y), owner))
                                self.positions.add((self.x, self.y))
                                print(f"MY BOX ON ({self.x}, {self.y})!")
                                for dx in [-1, 0, 1]:
                                    for dy in [-1, 0, 1]:
                                        neighbor = (self.x + dx, self.y + dy)
                                        if neighbor not in self.path:
                                            self.path.append(neighbor)
                            break


    def search_key_around(self,moves,limit_x1, limit_x2, limit_y1, limit_y2):
        """Teste les 8 cases autour"""
        print("KEY PATTERN")
        directions = [3, 2, 4, 4, 1, 1, 3, 3]
        
        for d in directions:
            dx, dy = moves.get(d, (0,0))

            x = self.x + dx
            y = self.y + dy
            if limit_x1 <= x < limit_x2 and limit_y1 <= y < limit_y2:
                print("LIMIT")
                self.network.send({"header": MOVE, "direction": d})
                sleep(0.2)
            
            else :
                self.network.send({"header": MOVE, "direction": 0})

            if self.cell_val == KEY_NEIGHBOUR_PERCENTAGE:
                print("je suis dans le if apres le d")
                directions = [3, 2, 4, 4, 1, 1, 3, 3]
                for i in directions:
                    dx, dy = moves.get(i, (0,0))

                    x = self.x + dx
                    y = self.y + dy

                    if limit_x1 <= x < limit_x2 and limit_y1 <= y < limit_y2:
                        print("LIMIT")
                        self.network.send({"header": MOVE, "direction": i})
                        print(f"i : {i} cell value : {self.cell_val}")
                        sleep(0.2)
                
                    else :
                        self.network.send({"header": MOVE, "direction": 0})
            
                    if  self.cell_val == 1.0:
                        info = self.request_item_owner()
                        owner = info.get("owner")
                        item_type = info.get("type")
                        
                        if item_type == KEY_TYPE:
                            if owner is not None and owner != self.agent_id:    # NOT THE ID KEY
                                self.foreign_items.add((self.x, self.y, owner, KEY_TYPE))  #say position, id and type of the key
                                self.positions.add((self.x, self.y))  #save position of the key (used after to not turn around the key because of the pattern)
                                print(f"not my key on ({self.x}, {self.y}), owner: {owner}")
                                
                                for dx in [-1, 0, 1]:
                                    for dy in [-1, 0, 1]:
                                        neighbor = (self.x + dx, self.y + dy)
                                        if neighbor not in self.path:
                                            self.path.append(neighbor)
                                
                            else:
                                self.my_key_found = True
                                self.KEYS_coordonates.append(((self.x, self.y), owner))
                                self.positions.add((self.x, self.y))
                                print(f"MY KEY FOUND ON ({self.x}, {self.y})!")

                                for dx in [-1, 0, 1]:
                                    for dy in [-1, 0, 1]:
                                        neighbor = (self.x + dx, self.y + dy)
                                        if neighbor not in self.path:
                                            self.path.append(neighbor)

                            break


    def avoid_pattern(self): 
        for dx in [-2, -1,0, 1,2]:
            for dy in [-2,-1,  0, 1, 2]:
                if dx == 0 and dy == 0:
                    continue
                neighbor_pos = (self.x + dx, self.y + dy)
                if neighbor_pos in self.positions:
                    return True
        return False
            
#added : 
    #algo d'évitement d'obstacle
    def go_to_goal(self, goal):
        while self.x != goal[0] and self.y != goal[1] and self.running:
            dx = goal[0] - self.x
            dy = goal[1] - self.y
            d = np.sqrt((goal[0] - self.x)**2 + ((goal[1] - self.y)**2))
            denom = d/2
            move = (int(dx/denom), int(dy/denom))
            #if there is a wall
            if self.cell_val == 0.35:
                go_back = (previous_move[0]*(-1), previous_move[1]*(-1))
                move = go_back
                direction = self.move_to_str[move]
                cmds = {"header": MOVE, "direction": direction}
                #go back 2 times
                self.network.send(cmds)
                sleep(0.2)
                self.network.send(cmds)
                sleep(0.2)


                #compute avoiding direction in function of the previous move
                avoid_direction_x = (dx/abs(dx))
                avoid_direction_y = (dy/abs(dy))

                if previous_move[0] == 0:
                    avoid_direction = (avoid_direction_x,0)
                elif previous_move[1] == 0:
                    avoid_direction = (0,avoid_direction_y)
                else:
                    if dy > dx:
                        avoid_direction = (0,avoid_direction_y)
                    else:
                        avoid_direction = (avoid_direction_x, 0)
                

                move = avoid_direction
                direction = self.move_to_str[move]
                
                for i in range(2):
                    cmds = {"header": MOVE, "direction": direction}
                    #do avoiding direction
                    self.network.send(cmds)

                    sleep(0.2)

                    #if avoiding direction is obstacle, change the avoiding direction
                    if self.cell_val == 0.35:
                        break
                        # move = (avoid_direction[0]*(-1), avoid_direction[1]*(-1))
                        # direction = self.move_to_str[move]
                    


            else:
                direction = self.move_to_str[move]
                cmds = {"header": MOVE, "direction": direction}
                self.network.send(cmds)

            previous_move = move
            #print(self.msg)

            sleep(0.2)


 
if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    try : 
        sleep(5)  
        limit_x, limit_y = agent.choose_map_division()
        limit_x1 = limit_x[0]
        limit_x2 = limit_x[1]
        limit_y1 = limit_y[0]
        limit_y2 = limit_y[1]
        print("limit x2", limit_x2)
        print("Je part vers mon départ")
        agent.go_to_goal((limit_x2-2, limit_y2-4)) # Ce met en bas à gauche  
        print("Je suis arrivé à mon départ")
        while True: 
            agent.move_diagonal(limit_x1, limit_x2, limit_y1, limit_y2)
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
