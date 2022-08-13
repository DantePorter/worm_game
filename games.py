import copy, random

__all__ = ["WHITE","GREY","BLACK","RED","GREEN","PURPLE","BLUE_LIGHT","YELLOW",
           "Worm", "Game","Game2","INTERVAL","BLOCK_SZ","SMALL_BLOCK","ROW_N","COL_N",
           "WIN_WIDTH","WIN_HEIGHT","SIZE"]

"""This module contains Game objects for verses and coop modes"""

#Variables for game's window
WIN_WIDTH = 640
WIN_HEIGHT = 480
SIZE = (WIN_WIDTH,WIN_HEIGHT)

WHITE = (255,255,255)
GREY = (128,128,128)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (51,255,51)
PURPLE = (204, 0, 255)
BLUE_LIGHT = (102,153,255)
YELLOW = (255,255,102)

# Grid size is manipulated by changing Interval
INTERVAL = 20
BLOCK_SZ = (21, 21)
SMALL_BLOCK = BLOCK_SZ[0] // 2
ROW_N = WIN_HEIGHT // INTERVAL
COL_N = WIN_WIDTH // INTERVAL

# Data used for beginning of game
START1 = [{'row': 2, 'col': 27}, {'row': 2, 'col': 28}, {'row': 2, 'col': 29}]
START2 = [{'row': 21, 'col': 4}, {'row': 21, 'col': 3}, {'row': 21, 'col': 2}]
DIRECTION1 = ('col', -1, 'Left')
DIRECTION2 = ('col', 1, 'Right')


class Game:
    #Initial starting points for players
    STARTS = [START1,START2]
    COLORS = [(YELLOW,GREEN),(BLUE_LIGHT,PURPLE)]
    COLORS2= [YELLOW,BLUE_LIGHT]   #Colors for apples when more than 1 player
    DIRECTIONS = [DIRECTION1,DIRECTION2]

    def __init__(self):
        self.n_players = 0
        self.players = []
        self.scores = []
        self.alive = []
        self.apples = []
        self.states = {'Playing':True,'Game Over':False}

    def reset(self,score_flag=True):
        self.states['Game Over'] = False
        res = False
        if score_flag:
            self.scores.clear()
        else:   #Used in two player verses
            res = True
            temp_score = self.scores
            tmp_count = self.n_players
        self.players.clear()
        self.alive.clear()
        self.apples.clear()
        self.n_players = 0
        if res:
            self.add_players(tmp_count)
            self.scores = temp_score

    def is_game_over(self):
        if not any(self.alive): self.states['Game Over'] = True

    def move_players(self,events):
        for p_id in events.keys():
            player = self.players[p_id-1]
            if player.alive:
                player.d = events[p_id]
                player.move()
                self.is_alive(player.player_id-1)

    def update(self,p_ids,events):
        self.move_players(events)
        self.is_game_over()

        # For 1 player game no need to check colliding heads condition
        if self.n_players > 1:
            heads_collided = self.has_heads()
        else: heads_collided = False
        if heads_collided: self.reset(score_flag=False)
        self.eaten(p_ids)

    def eaten(self, p_ids):
        for p_id in p_ids:
            head = 0
            player = self.players[p_id]
            head_pair = tuple(player.worm[head].values())
            for i in range(len(self.apples)):
                apple = self.apples[i]
                if head_pair == apple.coords:
                    if len(self.players)==1:   #For one player
                        self.help_eaten(player,apple,i)
                    elif player.colors[0] == apple.color:
                        self.help_eaten(player, apple, i)
                    else:
                        self.remove_score(p_id,apple,i)

    def help_eaten(self, player, apple, index):
        player.worm.append(player.worm[-1])
        self.scores[player.player_id-1] += 1
        color = apple.color
        self.add_apple(color,index)

    def remove_score(self,p_id,apple,index):
        self.players[p_id].worm.pop()
        if len(self.players[p_id].worm) < 2:
            self.alive[p_id] = False
            self.players[p_id].alive = False
        if self.scores[p_id] > 0: self.scores[p_id] -= 1
        self.add_apple(apple.color,index)

    def is_alive(self,p_id):
        """Check if anything has killed a player"""
        if not self.alive[p_id]: return
        bodies = self.ps_coords(1)  # grid coords of each worm
        p = self.players[p_id]
        head_pair = tuple(p.worm[0].values())
        head_x = p.worm[0]['col'] * BLOCK_SZ[0]
        head_y = p.worm[0]['row'] * BLOCK_SZ[0]

        if head_pair in bodies or head_x < 0 or \
                p.worm[0]['col'] >= COL_N or \
                head_y < 0 or p.worm[0]['row'] >= ROW_N:
            self.alive[p_id] = False
            self.players[p_id].alive = False

    def add_players(self,count):
        """Purpose: method adds players to game object based on count,and their
           corresponding alive, score and apple values are updated.
        """
        curr_count = len(self.players)
        for i in range(count):
            start = copy.copy(self.STARTS[curr_count])
            self.players.append(Worm(curr_count+1,start, self.COLORS[curr_count],
                                     self.DIRECTIONS[curr_count]))
            curr_count+=1
        self.create_apples(count)
        self.n_players += count
        self.alive = self.alive + ([True] * count)
        self.scores = self.scores + ([0] * count)

    def create_apples(self,count):
        coords = self.ps_coords(0)
        if count == 1:   #A game for one player where the apple is red
            self.apples.append(Apple(RED, coords))
        else:
            for n in range(count):
                new_apple = Apple(self.COLORS2[n],coords)
                coords.append(new_apple.coords)
                self.apples.append(new_apple)

    def add_apple(self,color,index):
        a_coords = [a.coords for a in self.apples]
        new_apple = Apple(color, self.ps_coords(0) + a_coords)
        self.apples[index] = new_apple

    def ps_coords(self, start):
        """Purpose: get players coordinates
           Parameters: start <-- use 0 to start from the head or 1 for the body
           return: a list of dictionaries used to track head and body on grid
         """
        return [tuple(player.worm[i].values()) for player in self.players
                for i in range(start,len(player.worm))]

    def has_heads(self):
        """Check if players heads have collided"""
        head_pairs = [tuple(p.worm[0].values()) for p in self.players]
        return head_pairs[0] == head_pairs[1]

class Game2(Game):
    """For a coop game play"""
    def __init__(self):
        super().__init__()
        self.scores = []
        #self.switch is toggled when apple is eaten
        self.switch = False
        self.apple = None

    def help_eaten(self,player,apple,index):
        player.worm.append(player.worm[-1])
        self.scores[0] += 1
        color = apple.color
        self.add_apple(color,index)
        self.switch = True

    def remove_score(self,p_id,apple,index):
        self.players[p_id].worm.pop()
        if len(self.players[p_id].worm) < 2:
            self.alive[p_id] = False
        if self.scores[0] > 0: self.scores[0] -= 1
        self.add_apple(apple.color, index)
        self.switch = True

    def is_game_over(self):
        if not all(self.alive): self.states['Game Over'] = True

    def update(self,p_ids,events,new_game=False):
        super().update(p_ids,events)
        if new_game: self.apple = random.choice(self.apples)

        if self.switch:   #Replace objective apple when eaten
            self.apple = random.choice(self.apples)
            self.switch = False

    def add_players(self,count):
        super().add_players(count)
        self.apple = random.choice(self.apples)

class Worm:
    def __init__(self, player_id, worm, colors, direction):
        self.player_id = player_id
        self.worm = worm  #worm is the data (list) used to track the head and body on grid
        self.colors = colors
        self.d = direction
        self.alive = True

    def move(self):
        del self.worm[-1]
        new_head = copy.copy(self.worm[0])
        new_head[self.d[0]] += self.d[1]
        self.worm = [new_head] + self.worm

class Apple:
    def __init__(self, color, players_coord):
        self.color = color
        self.coords = self.spawn_apple(players_coord)

    def spawn_apple(self, coords):
        """This function gets the coords for a new apple.
           The function makes sure the apple doesn't spawn on a snake."""
        while True:
            row = random.randint(0, ROW_N-1)
            col = random.randint(0, COL_N-1)
            if (row,col) not in coords:
                return (row,col)
