from socket import *
from queue import Queue
import pickle,threading
from network import ServerGame
from games import *
import time

"""This script hosts local online worm games: coop and verses modes.
   Data for a game and player connections is stored in ServerGame objects 
   from network.py.
   Note: the global variable ip_addr MUST be set to a local IP of hosting 
   machine. Also, for any given game, three threads will be running: two 
   communication threads that listen for players' responses and a thread
   for handling game logic and sending the updated game back to players.
"""

#ip_addr = str(gethostbyname(gethostname()))
ip_addr = "192.168.1.67"
port = 5555
welcomeSocket = socket(AF_INET, SOCK_STREAM)

#Variables used to track hosted games
games = {} #key <-- gameId; value <-- ServerGame
gameId = 0
invalidGIDs = [] #Game ids no longer valid

def waitConn(gID):
    """Purpose: Maintain a connection with first player in waiting lobby
       Parameters: gID <-- gameId for identifying a ServerGame object
       Post: If player left lobby then connection is closed
    """

    client0 = games[gID].getClient(0)

    message = client0.recv(1024).decode()

    if message == "Dead": #check if client left lobby (waiting screen)
        client0.send("Bye".encode())
        # notify runGame thread that client has left
        invalidGIDs.append(gID)
        waitCondition = games[gID].getCondition()
        waitCondition.acquire()
        waitCondition.notify()
        waitCondition.release()
        print("Closing waitConn thread bc client left")
        client0.close()
    elif message == "Ready":
        print("Closing waitConn thread bc game ready")
    else:
        print("Dont recognize message")
        client0.close()

def gameConn(pID, servGame):
    """Purpose: Maintain a connection with a player while in game.
                gameConn is a communication thread that notifies runGame
                thread of player's move.
       Parameters: pID (Int) <-- identifies player
                   servGame (ServerGame) <-- Used to host players' game
    """

    conn = servGame.getClient(pID)
    alive = True

    while alive:
        try:
            move = pickle.loads(conn.recv(1024))
        except EOFError:
            move = "Dead" #Game over; player out of moves

        if move == "Dead":
                alive = False
                servGame.gameConns += 1
        else:
            servGame.putMove(move)
        servGame.notify() #Notify runGame thread of player's move/choice

    print(f"gameConn thread for player {pID} is closing")

def responseConn(pID, servGame):
    """Purpose: Maintain a connection with a player while in game over screen.
                Get player's response: both 'menu' & 'quit' means game won't
                be restarted, as in False, whereas 'restart' means True.
                responseConn is a thread that notifies runGame thread.
       Parameters: pID (Int) <-- identifies player
                   servGame (ServerGame) <-- Used to host Players' game
    """
    conn = servGame.getClient(pID)
    response = pickle.loads(conn.recv(1024))
    servGame.addResponse(pID, response)
    servGame.notify()
    print(f"responseConn thread closing for {pID} with {response}")

def runGame(gID):
    """Purpose: Main thread for a server game """

    servGame = games[gID]
    client0 = servGame.getClient(0)
    client0.send(pickle.dumps(True))
    waitThread = threading.Thread(target=waitConn, args=(gID,))
    waitThread.start()

    #wait on a notification either from waitThread or main server thread
    waitCondition = servGame.getCondition()
    waitCondition.acquire()
    waitCondition.wait()
    waitCondition.release()

    if servGame.gameReady:
        if servGame.getMode() == "Coop":
            game = Game2()
        else: #Create verses game
            game = Game()

        p1 = client0
        p1.send("Ready".encode()) #let player 1 know a game was found
        p2 = servGame.getClient(1)
        p2.send(pickle.dumps(False)) #let player 2 know they don't have to wait

        while game.states["Playing"]:
            game.add_players(2)

            #Before starting game send game object so players get their direction
            time.sleep(1.5)
            p1.send(pickle.dumps(game))
            p2.send(pickle.dumps(game))

            gameCondition = waitCondition

            #start game connection threads
            p1Thread = threading.Thread(target=gameConn,args=(0,servGame))
            p2Thread = threading.Thread(target=gameConn,args=(1,servGame))
            p1Thread.start()
            p2Thread.start()

            servGame.state = "Playing"
            while not game.states["Game Over"]:
                with gameCondition: #Wait on both players moves
                    gameCondition.wait_for(lambda: servGame.getQsize() == 2)
                    moves = servGame.getMoves()


                if all(list(moves.values())) : #check if both players are still
                                              #playing. Note: a player has left
                                              #if there move is 'None'
                    game.update([0,1],moves)
                    p1.send(pickle.dumps(game))
                    p2.send(pickle.dumps(game))

            #start game over connection threads
            #Wait on gameConn threads to exit
            #Get players responses: restarting or left the lobby
            with gameCondition:
                gameCondition.wait_for(lambda: servGame.gameConns == 2)
                p1RespThread = threading.Thread(target=responseConn,
                                                args=(0,servGame))
                p2RespThread = threading.Thread(target=responseConn,
                                                args=(1,servGame))
                p1RespThread.start()
                p2RespThread.start()

            if servGame.isContin():
                servGame.restart()
                game.reset()
                game.states["Game Over"] = False
            else:
                game.states["Playing"] = False

            servGame.sendResponses(game) #send final game state to players

        p1.close()
        p2.close()


    games.pop(gID)
    if gID not in invalidGIDs:
        invalidGIDs.append(gID)
    print("Closing runGame thread")


def isReady():
    """Purpose: Check if server can be bound to ip address and port
       Return: ready (Boolean)
    """
    ready = False

    #Check ip & port binding for server
    try:
        welcomeSocket.bind((ip_addr,port))
        welcomeSocket.listen()
        ready = True
        print(f"Serving on {ip_addr}:{port}")
    except:
        print("Failed to start up server")
    return ready

def helpSetup(conn, gameMode):
    """Purpose: helper function for setUpGame.
       Parameters: conn <-- socket connection to player
                   gameMode <-- either 'Coop' or 'Verses'
       Post: gameId (Int) <-- increment by one
    """
    global gameId

    waitCondition = threading.Condition()
    games[gameId] = ServerGame(conn, gameMode, waitCondition)
    verseThread = threading.Thread(target=runGame, args=(gameId,))
    verseThread.start()
    gameId += 1

def setUpGame(q, gameMode, player):
    """Purpose: creates a ServerGame object
       Parameters: q (Queue) <-- either a queue of unmatched verses games
                                 or coop
                    gameMode <-- either 'Coop' or 'Verses'
                    player <-- socket connection
       Post: q is updated (from main server thread) and games is updated
    """

    if not q.empty(): #check if a player is waiting on a game queue
        currentID = q.get()
        if currentID not in invalidGIDs:
            servGame = games[currentID]
            servGame.gameReady = True
            servGame.addClient(player)
            readyCondition = servGame.getCondition()
            with readyCondition:
                readyCondition.notify()
        else: #currentID no longer exists; recent player left lobby; add to queue
            q.put(gameId)
            helpSetup(player, gameMode)
    else: #No lobby found for player, therefore add them to queue
        q.put(gameId)
        helpSetup(player, gameMode)

def main():
    """
    Main server thread that accepts new players and initializes a hosted game
    """
    unmatchVerse = Queue()
    unmatchCoop = Queue()

    while True: #Main server loop
        conn, addr = welcomeSocket.accept()
        print(f"Client {addr} has joined the server.")
        gameMode = conn.recv(1024).decode()

        if gameMode == "Coop":
            setUpGame(unmatchCoop, gameMode, conn)
        else: #other option is verses
            setUpGame(unmatchVerse, gameMode, conn)

if __name__ == "__main__":
    if isReady():
        main()