import pygame, sys
from pygame.locals import *
import pygame.freetype
from pygame.sprite import Sprite
from games import *
from network import Network
import pickle
import threading
import time

"""This script runs the worm game"""

pygame.init()
SCREEN = pygame.display.set_mode(SIZE,0,32)
pygame.display.set_caption("Worm")
FPS = 15
clock = pygame.time.Clock()

#Constant values for menu animation
animation_font = pygame.font.Font('freesansbold.ttf', 60)
word1_anim_sur = animation_font.render('Wormy!', True, GREEN, YELLOW)
word2_anim_sur = animation_font.render('Wormy!', True, PURPLE, None)
degrees1 = 0
degrees2 = 0

isKeyBoard = False #used when two players are using the same keyboard
BASICFONT = pygame.font.Font('freesansbold.ttf', 18)

player_LAN = None   #For LAN play

def handle_events(specific_events):
    """A decorator function for the various event functions"""
    def wrap_events(uiElems=None, in_menu=False, in_game=False,
                    game_over=False,players_d={}):
        for event in pygame.event.get():
            if event.type == QUIT: terminate()
            elif event.type == KEYDOWN and game_over:
                return specific_events(event)   #Invoke game_over_events
            elif event.type == KEYDOWN and in_game:
                specific_events(event, players_d)   #Invoke game_events
            elif event.type == MOUSEBUTTONDOWN and in_menu:
                return specific_events(uiElems)   #Invoke menu_events

    return wrap_events

@handle_events
def game_events(event, players):
    """Purpose: Check if player event-- i.e. direction-- is appropriate for
       change.
       Parameters: pygame event <-- is a key press
                   players <-- a dictionary of player ids (key) and directions (values)
       Post: return a dictionary: key is the p_id and value is a tuple which
             is the direction, and return an empty dictionary for no change
             in direction.
    """

    for p_id in players.keys():
        direction = players[p_id]  # current player's direction
        if p_id == 1:
            if event.key == K_RIGHT and direction[2] != 'Left':
                players[p_id] = ('col',1,'Right')
            elif event.key == K_LEFT and direction[2] != 'Right':
                players[p_id] = ('col', -1, 'Left')
            elif event.key == K_UP and direction[2] != 'Down':
                players[p_id] = ('row', -1, 'Up')
            elif event.key == K_DOWN and direction[2] != 'Up':
                players[p_id] = ('row',1,'Down')
        if p_id == 2:    #If condition is true then there is two players
            if event.key == K_d and direction[2] != 'Left':
                players[p_id] = ('col', 1, 'Right')
            elif event.key == K_a and direction[2] != 'Right':
                players[p_id] = ('col', -1, 'Left')
            elif event.key == K_w and direction[2] != 'Down':
                players[p_id] = ('row', -1, 'Up')
            elif event.key == K_s and direction[2] != 'Up':
                players[p_id] = ('row', 1, 'Down')

@handle_events
def menu_events(uiElems):
    for uiElem in uiElems:
        if uiElem.mouse_over:
            return uiElem.text
    else: return ''

@handle_events
def game_over_events(event):
    if event.key == K_m: return "menu"
    elif event.key == K_r: return "restart"
    elif event.key == K_q: return "quit"

refresh = lambda s: s.fill(BLACK)

def terminate():
    if player_LAN:
        player_LAN.client.send("Dead".encode())
    pygame.quit()
    sys.exit()

def update_py():
    pygame.display.update()
    clock.tick(FPS)

def draw_coop(game):
    """Draw for a 2 player coop setup"""
    draw_players(game)
    #for player in game.players:
        #if len(player.worm) > 1:  # Don't want to draw just a head
            #player.draw(screen)
    #if self.switch:
        #self.apple = random.choice(self.apples)
        #self.switch = False
    apple = game.apple
    y = apple.coords[0] * INTERVAL
    x = apple.coords[1] * INTERVAL
    apple_rect = pygame.Rect((x, y), BLOCK_SZ)
    pygame.draw.rect(SCREEN, apple.color, apple_rect)


def draw_score2(game):
    """Draw for a 2 player verses setup"""
    score1 = game.scores[0]
    score2 = game.scores[1]
    scoreSurf = BASICFONT.render('Score: ', True,WHITE)
    w = scoreSurf.get_width()
    scoreRect1 = scoreSurf.get_rect()
    scoreRect2 = scoreSurf.get_rect()
    scoreRect1.topleft = (45,10)
    scoreRect2.topleft = (WIN_WIDTH-120, 10)


    s1 = BASICFONT.render(f'{score1}',True,GREEN)
    s2 = BASICFONT.render(f'{score2}',True,PURPLE)
    s1Rect = s1.get_rect(); s1Rect.topleft = (w+44,10)
    s2Rect = s2.get_rect(); s2Rect.topleft = (WIN_WIDTH-(120-w),10)

    SCREEN.blit(scoreSurf,scoreRect1); SCREEN.blit(scoreSurf,scoreRect2)
    SCREEN.blit(s1,s1Rect); SCREEN.blit(s2,s2Rect)

def draw_score(score):
    """Draw for one player or coop setup"""
    scoreSurf = BASICFONT.render(f'Score: {score} ', True, WHITE)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (WIN_WIDTH - 120, 10)
    SCREEN.blit(scoreSurf, scoreRect)

def draw_grid():
    n = WIN_WIDTH//INTERVAL
    m = WIN_HEIGHT//INTERVAL

    for line in range(1,m):
        height = INTERVAL*line
        pygame.draw.line(SCREEN,GREY,(0,height),(WIN_WIDTH,height))
    for line in range(1,n):
        width = INTERVAL*line
        pygame.draw.line(SCREEN,GREY,(width,0),(width,WIN_HEIGHT))


def create_surface_with_text(text, font_size, text_rgb, bg_rgb):
    """ Returns surface with text written on """
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    #font = pygame.font.Font('freesansbold.ttf', font_size)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)
    return surface

class UIElement(Sprite):
    """ An user interface element that can be added to a surface """

    def __init__(self, center_pos, text, font_size, bg_rgb, text_rgb):
        """
        Args:
            center_position - tuple (x, y)
            text - string of text to write
            font_size - int
            bg_rgb (background colour) - tuple (r, g, b)
            text_rgb (text colour) - tuple (r, g, b)
        """
        self.mouse_over = False  # indicates if the mouse is over the element
        self.text = text
        # create the default image
        default_image = create_surface_with_text(
            text=text, font_size=font_size, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        # create the image that shows when mouse is over the element
        highlighted_image = create_surface_with_text(
            text=text, font_size=font_size * 1.2, text_rgb=text_rgb,
            bg_rgb=bg_rgb
        )

        # add both images and their rects to lists
        self.images = [default_image, highlighted_image]
        self.rects = [
            default_image.get_rect(center=center_pos),
            highlighted_image.get_rect(center=center_pos),
        ]

        # calls the init method of the parent sprite class
        super().__init__()

    # properties that vary the image and its rect when the mouse is over
    # the element
    @property
    def image(self):
        return self.images[1] if self.mouse_over else self.images[0]

    @property
    def rect(self):
        return self.rects[1] if self.mouse_over else self.rects[0]

    def update(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.mouse_over = True
        else:
            self.mouse_over = False

    def draw(self):
        """ Draws element onto a surface """
        SCREEN.blit(self.image, self.rect)

def menu_animation(w1,w2,d1,d2):
    rotatedSurf1 = pygame.transform.rotate(w1, d1)
    rotatedRect1 = rotatedSurf1.get_rect()
    rotatedRect1.center = (WIN_WIDTH / 2, WIN_HEIGHT / 4)
    SCREEN.blit(rotatedSurf1, rotatedRect1)

    rotatedSurf2 = pygame.transform.rotate(w2, d2)
    rotatedRect2 = rotatedSurf2.get_rect()
    rotatedRect2.center = (WIN_WIDTH / 2, WIN_HEIGHT / 4)
    SCREEN.blit(rotatedSurf2, rotatedRect2)

def run_menu(uiElems,texts,is_LAN):
    """uiElems --- is the options a user clicks on, and
                   this function returns an option.

       texts --- contains elements for drawing plaintext on screen
       is_LAN --- if player is on a LAN then 'talk' with server"""

    global degrees1, degrees2
    option = '' #Empty string means user hasn't selected an option
    while not option:
        SCREEN.fill(BLUE_LIGHT)
        option = menu_events(uiElems=uiElems,in_menu=True)
        menu_animation(word1_anim_sur, word2_anim_sur, degrees1, degrees2)
        if is_LAN:
            if player_LAN.is_waiting == False: option = "Ready"
        for text in texts:
            SCREEN.blit(text[0],text[1])
        for uiElem in uiElems:
            uiElem.update(pygame.mouse.get_pos())
            uiElem.draw()
        update_py()
        degrees1 += 3  # rotate by 3 degrees each frame
        degrees2 += 7  # rotate by 7 degrees each frame
    return option

def start_menu():
    #Block of code for create uiElems
    uiElem_x = WIN_WIDTH/2
    uiElem_y = (WIN_HEIGHT/2) + 65
    spacing = 35   #vertical spacing between uiElems
    uiFontSz = 30
    uiElem1 = UIElement((uiElem_x, uiElem_y),"1 Player", uiFontSz, None, WHITE)
    uiElem2 = UIElement((uiElem_x, uiElem_y + spacing),"2 Player", uiFontSz, None, WHITE)
    uiElem3 = UIElement((uiElem_x,uiElem_y + (2*spacing)),"Quit", uiFontSz, None, WHITE)
    uiElems = [uiElem3,uiElem2,uiElem1]

    return run_menu(uiElems,[],False)

def draw_press_key_msg():
    option1 = create_surface_with_text("Press m: menu", 18, WHITE, None)
    option2 = create_surface_with_text("Press r: restart", 18, WHITE, None)
    option3 = create_surface_with_text("Press q: quit", 18, WHITE, None)

    w3 = option3.get_width() + 3

    option1_r = option1.get_rect(x=3,y=WIN_HEIGHT-30)
    option2_r = option2.get_rect(centerx=WIN_WIDTH/2,y=WIN_HEIGHT-30)
    option3_r = option3.get_rect(x=WIN_WIDTH-w3,y=WIN_HEIGHT-30)

    SCREEN.blit(option1,option1_r)
    SCREEN.blit(option2,option2_r)
    SCREEN.blit(option3,option3_r)

def still_playing(game, choice):
    if player_LAN:
        result = False
        if choice == "quit" or choice == "menu":
            player_LAN.quit = True
        else:
            result = True
        player_LAN.client.send(pickle.dumps(result))
        return
    if choice == "menu": game.states['Playing'] = False
    elif choice == "restart": game.reset()
    elif choice == "quit": terminate()

def game_over_screen(game):
    gameSurf = create_surface_with_text('Game', 150, WHITE, None)
    overSurf = create_surface_with_text('Over', 150, WHITE, None)
    gameRect = gameSurf.get_rect()
    overRect = overSurf.get_rect()
    gameRect.midtop = (WIN_WIDTH / 2, 10)
    overRect.midtop = (WIN_WIDTH / 2, gameRect.height + 10 + 25)

    SCREEN.blit(gameSurf, gameRect)
    SCREEN.blit(overSurf, overRect)
    draw_press_key_msg()
    pygame.time.wait(500)
    pygame.display.update()

    choice = ''
    while not choice:
        choice = game_over_events(game_over=True)
    pygame.event.get()  #clear event queue
    still_playing(game, choice)

    return choice

def select_mode():
    x1 = WIN_WIDTH/4
    x2 = WIN_WIDTH * (3/4)
    y = (WIN_HEIGHT * (3/4)) - 20
    font_sz = 55
    uiElem1 = UIElement((x1,y), "Verses", font_sz, None, WHITE)
    uiElem2 = UIElement((x2,y+5), "Coop", font_sz, None, WHITE)
    uiElem3 = UIElement((35,WIN_HEIGHT-20),"Back",20,None,WHITE)
    uiElems = [uiElem1, uiElem2,uiElem3]

    return run_menu(uiElems,[],False)

def how_setup():
    uiElem_x = WIN_WIDTH/2
    uiElem_y = (WIN_HEIGHT/2) + 65
    spacing = 35   #vertical spacing between uiElems
    uiFontSz = 30
    uiElem1 = UIElement((uiElem_x, uiElem_y),"Local", uiFontSz, None, WHITE)
    uiElem2 = UIElement((uiElem_x, uiElem_y+spacing), "Online", uiFontSz, None, WHITE)
    uiElem3 = UIElement((35,WIN_HEIGHT-20),"Back",20,None,WHITE)
    uiElems = [uiElem1,uiElem2,uiElem3]

    return run_menu(uiElems,[],False)

def wait_screen():
    wait_text = create_surface_with_text("Waiting for other player...", 35, WHITE, None)
    wait_text_r = wait_text.get_rect(centerx=WIN_WIDTH/2,y=(WIN_HEIGHT / 2) + 65)
    uiElem1 = UIElement((35, WIN_HEIGHT - 20), "Menu", 20, None, WHITE)
    uiElems = [uiElem1]
    texts = [(wait_text,wait_text_r)]

    return run_menu(uiElems,texts,True)

def wait_thread():
    """This thread waits for a message from
    the server telling the client/player if another
    player was found."""

    message = player_LAN.client.recv(1024)

    if message.decode() == "Ready":
        player_LAN.is_waiting = False
        player_LAN.client.send("Ready".encode()) #send to close wait thread on
                                                 # server
        print("Exiting wait_thread bc a lobby was found")
    elif message.decode() == "Bye":
        print("Connection to server has been closed")
        print("Exiting wait_thread bc player left lobby" )
    else:
        print("Don't recognize message in wait_thread")

def verse(n_players,draw_mode):
    """A setup for 1 or 2 player game on the same computer"""
    game = Game()
    while game.states['Playing']:
        game.add_players(n_players)
        p_events = {game.players[i].player_id:game.players[i].d for i in
                    range(game.n_players)}
        p_ids = [i for i in range(game.n_players)]
        while not game.states['Game Over']:
            refresh(SCREEN)
            game_events(players_d=p_events, in_game=True)
            game.update(p_ids, p_events)
            draw_screen(game,draw_mode)
            update_py()
        game_over_screen(game)

def LAN_game(mode):
    """Connect to wormServer to play local online game; have player wait
       if no lobby is found
    """
    global player_LAN

    if mode == '2PV': name = "Verses"
    else: name = "Coop"
    player_LAN = Network(name)

    # Server tells client/player to wait if necessary
    is_waiting = pickle.loads(player_LAN.client.recv(1024))
    if is_waiting:
        player_LAN.is_waiting = True
        t1 = threading.Thread(target=wait_thread)
        t1.start()
        choice = wait_screen() #returns "Ready" or "Menu"
        if choice == "Menu":   #Player left matchmaking
            player_LAN.client.send("Dead".encode())
            player_LAN.client.close()
            del player_LAN
            player_LAN = None
        else:
            run_LAN(mode,1)  #Starting game for player 1
    else: run_LAN(mode,2)  #Starting game for player 2

def run_LAN(mode,p_id):
    """Communicate with server to facilitate local online game (either coop
       or verses)
    """
    global player_LAN
    starting = True

    while starting or game.states["Playing"]:
        starting = False
        conn_loss = False
        game = pickle.loads(player_LAN.client.recv(8192))
        p_event = {p_id:game.players[p_id-1].d}
        while not game.states["Game Over"]:
            refresh(SCREEN)
            game_events(players_d=p_event,in_game=True)
            player_LAN.client.send(pickle.dumps(p_event))
            game = pickle.loads(player_LAN.client.recv(8192))  #Updated game from server

            if game == b'':
                conn_loss = True
                game.states["Game Over"] = True
                game.states["Playing"] = False
            else:
                draw_screen(game,mode)
                update_py()
        if not conn_loss:
            player_LAN.client.send("Game Over".encode())
            time.sleep(1) #Wait on server to close gameConn threads
            choice = game_over_screen(game)
            if choice == "menu":
                game.states["Playing"] = False
            elif choice == "quit":
                terminate()
            else: #continue playing and wait on server response
                game = pickle.loads(player_LAN.client.recv(8192))

    player_LAN.client.close()
    player_LAN = None

def draw_screen(game,mode):
    """Purpose: General function for drawing grid,players, apples, and scores
       Parameters: game <-- game object tracks the state of game
                   mode <-- string that's used as an indicator for drawing score(s)
    """
    draw_grid()
    draw_players(game)
    if mode == "1P":
        draw_apples(game)
        draw_score(game.scores[0])
    elif mode == "2PV":   #Verses mode for 2 players
        draw_apples(game)
        draw_score2(game)
    elif mode == "2PC":    #Coop mode for 2 player
        draw_score(game.scores[0])
        draw_coop(game)

def draw_players(game):
    a = (BLOCK_SZ[0] - SMALL_BLOCK) // 2
    for p in game.players:
        # Draw the head first
        # Don't draw the head if dead (for 2 players)
        if p.alive:
            head_x = p.worm[0]['col'] * INTERVAL
            head_y = p.worm[0]['row'] * INTERVAL
            small_head_x = head_x + a
            small_head_y = head_y + a
            pygame.draw.rect(SCREEN, p.colors[0], pygame.Rect((head_x, head_y), BLOCK_SZ))
            pygame.draw.rect(SCREEN, p.colors[1], pygame.Rect((small_head_x, small_head_y),
                                                              (SMALL_BLOCK, SMALL_BLOCK)))

        # Draw body
        for i in range(1, len(p.worm)):
            limb_x = p.worm[i]['col'] * INTERVAL
            limb_y = p.worm[i]['row'] * INTERVAL
            small_limX = limb_x + a
            small_limY = limb_y + a
            pygame.draw.rect(SCREEN, p.colors[1], pygame.Rect((limb_x, limb_y), BLOCK_SZ))
            pygame.draw.rect(SCREEN, p.colors[0], pygame.Rect((small_limX, small_limY),
                                                                 (SMALL_BLOCK, SMALL_BLOCK)))

def draw_apples(game):
    for apple in game.apples:
        y = apple.coords[0] * INTERVAL
        x = apple.coords[1] * INTERVAL
        apple_rect = pygame.Rect((x, y), BLOCK_SZ)
        pygame.draw.rect(SCREEN, apple.color, apple_rect)


def coop_1():
    """A setup for 2 player coop on the same computer"""
    game = Game2()
    while game.states['Playing']:
        game.add_players(2)
        p_events = {game.players[i].player_id:game.players[i].d for i in range(game.n_players)}
        p_ids = [i for i in range(game.n_players)]
        while not game.states['Game Over']:
            refresh(SCREEN)
            game_events(players_d=p_events,in_game=True)
            game.update(p_ids,p_events)
            draw_screen(game,"2PC")   #2PCOn = 2 player coop on same screen
            update_py()
        game_over_screen(game)

def twoPlayer():
    choosing = True   #When a player(s) enter a game this is set to false
    while choosing:
        mode = select_mode()
        #mode = "Coop"
        if mode == 'Back':
            choosing = False
        else:
            setup = how_setup()
            #setup = "On computer"
            if setup != 'Back':
                choosing = False
                choice = mode[0] + setup[0]
                #choice = "CO"
                if mode[0] == 'V':
                    #2 player verses on same screen
                    if choice == 'VL': verse(2,'2PV')
                    #2 player verses on LAN
                    elif choice == 'VO': LAN_game('2PV')
                elif mode[0] == 'C':
                    #Coop mode on same computer
                    if choice == 'CL': coop_1()
                    #Coop on LAN
                    elif choice == 'CO': LAN_game('2PC')


if __name__ == "__main__":
    while True:
        startMenuChoice = start_menu()
        #startMenuChoice = '2 Player'
        if startMenuChoice == '1 Player': verse(1,"1P")
        elif startMenuChoice == '2 Player': twoPlayer()
        else: terminate()

