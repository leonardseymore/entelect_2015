Build Info
==========
This project does not use any dependencies

Project Structure
=================
All the AI logic sits in the 'ai' module, the rest of the source code is for testing purposes during development

Strategy
========
The high level strategy:
- Survive
- Shoot as many aliens as possible
- Build buildings as fast as possible in safe locations

A behavior tree is used to control the high level strategy:
1) If starting round then shoot
2) If no ship then do nothing
3) If in danger use a tree search to find best action
4) If we have spare lives
4.1) If we can shoot an alien right now then do so
4.2) Build missile controller behind open shield array
4.3) Build alien factory behind open shield array
5) Kill as many aliens as possible!
6) Check if the last move we made is dangerous and if so do a tree search to find the best action

To target aliens:
Tracer missiles are fired from the current ship position and moved forward for a number of turns to determine if they
hit any aliens. The bot then moves to and waits for the starting position and round for a tracer candidate to fire.