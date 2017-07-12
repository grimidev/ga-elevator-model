import numpy as np
import time
from ga import *

SETTINGS = {}

DEBUG = True

class passenger:
    def __init__(self, origin_floor, destination_floor, name, birth_time=time.time()):
        self.MAX_WAITING_TIME = 9999
        self.destination_floor = destination_floor
        self.birth_time = birth_time
        self.name = name
        self.quit_time = birth_time + self.MAX_WAITING_TIME
        self.origin_floor = origin_floor
        

class elevator:
    
    
    def __init__(self, floors_amount, capacity):
        self.direction = 'up'
        self.is_moving = False
        self.current_floor = 0
        self.destination_floor = 0
        self.passenger = []
        
        self.timer = {
            # movimento da un piano ad un altro
            'moving' : -1,
            
            # decelerazione + apertura_porte
            'move_to_stop' : -1,
            
            # chiusura_porte + accelerazione
            'stop_to_move' : -1,
            
            # caricamento_passeggeri + selezione_piano
            'loading' : -1,
            
            # scaricamento passeggeri
            'unloading' : -1
        }
        
        self.capacity = capacity
        self.floors_amount = floors_amount

    def isIdle(self):
        return [v for (_,v) in self.timer.items()].count(-1) == len(self.timer)

    def isEmpty(self):
        return len(self.passenger) == 0

    def updateDirection(self):
        if self.current_floor <= self.destination_floor:
            self.direction = 'up'
        else:
            self.direction = 'down'
            
    def updateDestinationFloor(self, destination_floor=None):
        if destination_floor == None:
            if self.direction == 'up':
                destination_floor = 0
                for p in self.passenger:
                    if p.destination_floor > destination_floor:
                        destination_floor = p.destination_floor
            elif self.direction == 'down':
                destination_floor = self.floors_amount-1
                for p in self.passenger:
                    if p.destination_floor < destination_floor:
                        destination_floor = p.destination_floor
            else:
                raise Exception("Elevator direction is neither up nor down")
                
        self.destination_floor = destination_floor
        self.updateDirection()
    
    def getOff(self):
        passenger_index = self.passengersGettingOff()
        new_passenger = []
        for i in range(len(self.passenger)):
            if i not in passenger_index:
                new_passenger.append(self.passenger[i])
        self.passenger = new_passenger
        
    
    def passengersGettingOff(self, floor=None):
        if floor == None:
            floor = self.current_floor
        
        getting_off = []
        for p in self.passenger:
            if p.destination_floor == floor:
                getting_off.append(p)
        return getting_off
    
    def load(self):
        self.timer["loading"] = SETTINGS["elevator"]["timing"]["loading"]
        
    def unload(self):
        self.timer["unloading"] = SETTINGS["elevator"]["timing"]["unloading"]
    
    def moveToStop(self):
        self.is_moving = False
        self.timer["move_to_stop"] = SETTINGS["elevator"]["timing"]["move_to_stop"]
        
    def stopToMove(self):
        self.is_moving = True
        self.timer["stop_to_move"] = SETTINGS["elevator"]["timing"]["stop_to_move"]
        
    def move(self):
        self.is_moving = True
        self.timer["moving"] = SETTINGS["elevator"]["timing"]["moving"]
    
class egc:
    def __init__(self):
        self.floor_queue = []
        self.elevator = []
        self.new_calls = False
        self.assignement = []
        
        self.nf = SETTINGS["floors_amount"]
        self.nc = SETTINGS["shafts_amount"]

        for _ in range(self.nc):
            self.elevator.append(elevator(self.nf, SETTINGS["elevator"]["capacity"]))
            
        for _ in range(self.nf):
            self.floor_queue.append([])
    
    
    def passengersGettingOn(self, elevator_id):
        getting_on = []
        
        el = self.elevator[elevator_id]
            
        if self.assignement[el.current_floor] == elevator_id:
            for i in range(len(self.floor_queue[el.current_floor])):
                p = self.floor_queue[el.current_floor][i]
                if p.destination_floor > el.current_floor:
                    getting_on.append(i)
            
        if self.assignement[int(el.current_floor + len(self.assignement)/2)] == elevator_id:
            for i in range(len(self.floor_queue[el.current_floor])):
                p = self.floor_queue[el.current_floor][i]
                if p.destination_floor < el.current_floor:
                    getting_on.append(i)
            
        return getting_on
    
    def getOn(self, elevator_id):
        passenger_index = self.passengersGettingOn(elevator_id)
        new_floor_queue = []
        
        el = self.elevator[elevator_id]
        
        for i in range(len(self.floor_queue[el.current_floor])):
            if i not in passenger_index:
                new_floor_queue.append(self.floor_queue[el.current_floor][i])
            else:
                el.passenger.append(self.floor_queue[el.current_floor][i])
                
        self.floor_queue[el.current_floor] = new_floor_queue
        
    
    def step(self):
        # elevator ID counter
        el_id = 0
        
        # loop through every elevator in self.elevator
        for el in self.elevator:
            # loop through every key in el.timer dictionary
            for key in el.timer:
                # timer equal to 0 it means some action have to occur
                if el.timer[key] == 0:
                    # switch to find which is the key equal to 0
                    
                    # if the key is 'moving'
                    if key == 'moving':
                        # then increment or decremtn the floor with regards to
                        # the direction (up or down respectively)
                        if el.direction == 'up':
                            el.current_floor += 1
                        elif el.direction == 'down':
                            el.current_floor -= 1
                        else:
                            # if the direction is neither up nor down
                            # then raise an exception
                            raise Exception("Unknown elevator direction")
                        
                        # flags:
                        # True if there is one or more incoming up calls at the
                        # current floor for the current elevator
                        up_call = False
                        # the same for incoming down calls
                        down_call = False
                        
                        # if the current floor is the lowest
                        if el.current_floor == 0:
                            # then check only up calls
                            # if that call is assigned to current el
                            if self.assignement[el.current_floor] == el_id:
                                # then set flag to true
                                up_call = True
                                
                        # if the current floor is the highest
                        elif el.current_floor == el.floors_amount-1:
                            # then check only down calls
                            if self.assignement[int(el.current_floor+len(self.assignement)/2)] == el_id:
                                down_call = True
                        
                        # else, that is current_floor is neither the lowest nor the highest
                        else:
                            # then check for both up and down calls
                            if self.assignement[el.current_floor] == el_id:
                                up_call = True
                            if self.assignement[int(el.current_floor+len(self.assignement)/2)] == el_id:
                                down_call = True
                        
                        # if there is one or more passenger in the elevator who need to get off
                        # or if there are up or down calls at the current floor
                        if len(el.passengersGettingOff()) > 0 or up_call or down_call:
                            # then stop (that is decelerate, stop and open doors)
                            el.moveToStop()
                        else:
                            # else conitnue moving upward or downward
                            el.move()
                        
                    elif key == 'move_to_stop':
                        # TODO: scegliere l'azione da intraprendere
                        # load / unload
                        # unload: scarica se qualche passeggero ha come destinazione il piano corrente
                        
                        # if there is one or more passenger in the elevator who needs to get off
                        if len(el.passengersGettingOff()) > 0:
                            el.unload()
                            
                        # else if there is one or more passenger who needs to get on 
                        elif len(self.passengersGettingOn(el_id)):
                            el.load()
                            
                    elif key == 'stop_to_move':
                        # azione di movimento
                        el.move()
                        
                    elif key == 'loading':
                        # p = self.floor_queue[el.current_floor].dequeue()
                        # el.passenger.append(p)
                        # el.timer['stop_to_move'] = H
                        self.getOn(el_id)
                        el.stopToMove()
                        self.updateElevatorsDestinationFloor()
                        
                    elif key == 'unloading':
                        # p = el.passenger.dequeue()
                        # self.floor_queue[el.current_floor].enqueue(p)
                        # el.timer['move_to_stop'] = L
                        el.getOff()
                        
                        if len(self.passengersGettingOn(el_id)) > 0:
                            el.load()
                        else:
                            el.stopToMove()
                        
                        self.updateElevatorsDestinationFloor()
                    else:
                        raise KeyError("Unknown elevator timer key in step function")
                
                if el.timer[key] >= 0:
                    if DEBUG:
                        print(">>> ELEVATOR with id=" + str(el_id) + " timer[" + key + "]-=1")
                    el.timer[key] -= 1
            el_id += 1
        
        #Se abbiamo nuove chiamate:
        if self.new_calls:
            if DEBUG:
                print("New calls incoming")
            # Passive Time
            pt = 1 ################################## TODO
            # Inter floor trip time
            it = 3
            
            # Hall call UP/DOWN
            hcu = np.zeros(self.nf)
            hcd = np.zeros(self.nf)
            f = 0
            for p_waiting_at_f in self.floor_queue:
                for p in p_waiting_at_f:
                    if p.destination_floor > p.origin_floor:
                        hcu[f] = 1
                    elif p.destination_floor < p.origin_floor:
                        hcd[f] = 1
                    else:
                        raise Exception("Passenger destination_floor == origin_floor")
                f += 1
    
            cf = []
            cdf = []
            for el in self.elevator:
                cf.append(el.current_floor)
                cdf.append(el.destination_floor)
            
            self.assignement = ga(self.nf, self.nc, pt, it, list(hcu), list(hcd), cf, cdf).computeSolution()
            self.new_calls = False
            self.updateElevatorsDestinationFloor()

        for el in self.elevator:
            if el.isIdle():
                if el.destination_floor != el.current_floor:
                    el.stopToMove()
        

    def updateElevatorsDestinationFloor(self):
        for i in range(len(self.elevator)):
            el = self.elevator[i]
            el_id = i
            if el.isEmpty():
                el_call = []
                el_call_distance = []
                for j in range(len(self.assignement)):
                    call_el_id = self.assignement[j]
                    """
                    [ -1, -1, +0, -1, -1 |||| -1, -1, -1, -1, +1 ]
                    """
                    if call_el_id == el_id:
                        # se j < len(...) allora è nella prima metà dell'assignement
                        # quindi il piano della chiamta è semplicemente j
                        call_floor = j
                        # altrimenti se j è nella seconda metà degli assignment,
                        # per trovare il piano effettivo
                        # dobbiamo sottrarre metà della lunghezza dell'array e aggiungere
                        # 1 per trovare il piano reale di chiamata
                        if j >= len(self.assignement)/2:
                            call_floor = j - len(self.assignement)/2
                        
                        el_call.append(call_floor)
                        el_call_distance.append(abs(el.current_floor - call_floor))
                if len(el_call_distance) > 0:
                    el.updateDestinationFloor(el_call[el_call_distance.index(min(el_call_distance))])
            else:
                el.updateDestinationFloor()


class model:
    def __init__(self):
        self.time = 0
        self.egc = egc()
        
    
    # pass di tempo discreto da t a t+1
    def step(self):
        # generazione passeggeri
        '''
        origin = np.random.randint(SETTINGS["floors_amount"])
        destination = np.random.randint(SETTINGS["floors_amount"])
        while destination == origin:
            destination = np.random.randint(SETTINGS["floors_amount"])
        p = passenger(origin, destination)
        self.egc.floor_queue[origin].append(p)
        '''
        self.egc.step()
    
    # lancia gli step in successione
    def start(self):
        while (self.time < 1000): #temp
            if self.time == 1:
                p = passenger(2, 0, "Rondine")
                self.egc.floor_queue[2].append(p)
                self.egc.new_calls = True
            if self.time == 3:
                p = passenger(1, 4, "Amed")
                self.egc.floor_queue[1].append(p)
                self.egc.new_calls = True
            self.step()
            self.printModel()
            input("Press button to continue...")
            self.time += 1

    def printModel(self):
        print("------- MODEL -------")
        print("TIME=" + str(self.time))
        print("ASSIGNEMENT=" + str(self.egc.assignement))
        
        print("\n------- ELEVATORS -------")
        for i in range(len(self.egc.elevator)):
            el = self.egc.elevator[i]
            p_names = [p.name for p in el.passenger]
            print(str.format("Elevator {0} => current_floor={1} - destination_floor={2} - passengers={3}", i, el.current_floor, el.destination_floor, p_names))
            print("\t" + str(el.timer))
            
        print("\n------- FLOOR QUEUE -------")
        for i in range(len(self.egc.floor_queue)):
            queue = self.egc.floor_queue[i]
            p_names = [p.name for p in queue]
            print(str.format("Floor {0} => passengers={1}", i, p_names))

if __name__ == '__main__':
    # random seed
    np.random.seed(0)
    
    SETTINGS = {
        "shafts_amount" : 3,
        "floors_amount" : 10,
        "elevator" : {
            "capacity" : 5,
            "timing" : { # in seconds
                # movimento da un piano ad un altro
                'moving' : 3,
                
                # decelerazione + apertura_porte
                'move_to_stop' : 3,
                
                # chiusura_porte + accelerazione
                'stop_to_move' : 3,
                
                # caricamento_passeggeri + selezione_piano
                'loading' : 5,
                
                # scaricamento passeggeri
                'unloading' : 3
            }
        },
        "passenger" : {
            "max_waiting_time" : 300 # secondi
        }
    }
    
    model = model()
    model.start()