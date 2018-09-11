Outline


Stack
Front-end: CoffeeScript, jQuery, ????
Webservers: Tornado, Python
Communication Layer: Redis
GameEngine: Python
Permanent Storage: MongoDB?


MongoDB stores:
Players
    Scripts played
Games
    Stats
Ratings
Scripts
Tragedy Sets
Plots
Characters
Roles
Incidents


Redis communicates:
Lobby activity
Chats
Game states
Requests to take action
Player actions


Webserver:


GameEngine:


tragedy sets info:
    plots
    constraints
    incidents


scripts info:
    tragedy set
    plots
    characters
    incidents
    constraints


game info:
    script
    board
    characters
    players
    protagonists
    leader
    extra gauge
    
    
player info:
    player id
    protagonist
    

characters info:
    name
    paranoia limit
    starting location
    current location
    traits
    prohibited locations
    starting paranoia
    starting intrigue
    starting goodwill
    starting role
    current paranoia
    current intrigue
    current goodwill
    current role
    false role
    current extra card
    revealed
    dead
    abilities
    
roles info:
    name
    public name
    goodwill refusal
    abilities
    
abilities info:
    window
    goodwill
    mastermind
    owner
    target traits

triggers info:
    window
    effect
    last_triggered
    owner
    target traits
    
passives
    window
    owner
    target traits