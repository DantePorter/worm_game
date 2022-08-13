from socket import *
import pickle, queue

"""This module contains two networking objects: Network is used by the client
   and ServerGame is used by the server. These objects contain sockets and
   other relevant data for a game. Note: Network object MUST have the
   same local ip as the server, modify as needed.
"""


class Network:
    """Network is an interface between the server and worm
    (client). A client will send event data, while the server
    sends a game object."""

    def __init__(self,game):
        self.client = socket(AF_INET, SOCK_STREAM)
        self.server = "192.168.1.67"
        #self.server = str(gethostbyname(gethostname()))
        self.port = 5555
        self.game_mode = game  #Is a string not a game object
        self.quit = False   #While playing if player hits 'q' then set to False
        self.is_waiting = False #If player is in the waiting screen
        self.p_id = self.connect()  #player id

    def getP_id(self):
        return self.p_id

    def connect(self):
        try:
            self.client.connect((self.server,self.port))
            self.client.send(self.game_mode.encode())
        except:
            print('Failed')

class ServerGame:
    """Data object: stores client sockets and other data related to
       a game ran in the server
     """

    def __init__(self,client0, gameMode, condition):
        self.conns = [client0] #list of client connections; position is first client0
        self.gameMode = gameMode # Coop or Verses
        self.gameCond = condition #Used by server threads; read wormServer.py
                                  #for more details
        self.gameConns = 0 #A tally of gameConn threads that have finished
        self.gameReady = False
        self.responses = {} #used when players are in game over screen
                            #key <-- player's id; value <-- True means 'restart'
                            #                     otherwise False
        self.playersMoves = queue.Queue(2)

    def addClient(self, newClient):
        self.conns.append(newClient)

    def getMode(self):
        return self.gameMode

    def getClient(self, playerId):
        return self.conns[playerId]

    def getCondition(self):
        """Return threading.Condition object"""
        return self.gameCond

    def putMove(self, move):
        """A players moves has the following form: {[playerId]: {worm body}"""
        with self.gameCond:
            self.playersMoves.put(move)

    def getMoves(self):
        moves = {}

        sz = self.playersMoves.qsize()
        for _ in range(sz):
            moves.update(self.playersMoves.get())
        return moves

    def notify(self):
        with self.gameCond:
            self.gameCond.notify()

    def getQsize(self):
        """Used as a condition for determining when both players have sent
           there moves
        """
        return self.playersMoves.qsize()

    def addResponse(self, pID, resp):
        """Add players responses during game over screen"""
        self.responses[pID] = resp

    def sendResponses(self, game):
        for p in self.responses:
            if self.responses[p]:
                self.conns[p].send(pickle.dumps(game))
                print(f"sent final game to player {p}")
        self.responses = {}

    def isContin(self):
        """Before continuing, check that both players have sent their responses
           while in game over screen
        """
        with self.gameCond:
            self.gameCond.wait_for(lambda: len(self.responses.values()) == 2)
        return all(self.responses.values())

    def restart(self):
        self.playersMoves = queue.Queue(2)
        self.gameConns = 0

