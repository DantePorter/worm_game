# worm_game
  This project contains a game called wormy (Yes, I know, cheesy but I learned a lot from this project!). The game is simple: players are worms
  seeking apples to gain points. Since the game has local online play, two players can face off against eachother or cooperate on the task of 
  collecting apples.Python and Pygame were chosen in making the game. I'll admit, the code lacks a good design pattern, so game 
  components like rendering the screen and handling game events or logic were all placed in the same file, called wormGame.py. Indeed, when 
  first starting the project, I had no knowledge of game design patterns and a tenous grasp on other concepts like networking and multithreading, 
  all of which created for poor separation and messy code. If I redo the project in the future then I'd use a model controller design, and scale
  the game by allowing more players in a game, instead of two players maybe 4, for example.
  
# What I learned
  1) Network programming
  2) Multithread programming
  3) Developed more OOP skils
  4) Decorator functions
  5) How to design and implement a client-server archeticture
  
# Getting started
  Run wormGame.py using a python interpreter 3 plus and make sure pygame is installed using pip. For multiplayer the wormServer.py must be running
  then the players (after running wormGame.py) can play locally.
  
