#Artificial Intelligence Goals#

From [Wikipedia](https://en.wikipedia.org/wiki/Artificial_intelligence?oldformat=true):

    The central problems (or goals) of AI research include reasoning, knowledge,
    planning, learning, natural language processing (communication), perception and
    the ability to move and manipulate objects.

Let's break these out into a list, and check off what we've already got in our MineCraft robot, and sort them from finished to unsolved:

- [x] perception
- [x] the ability to move and manipulate objects
- [ ] reasoning
- [ ] knowledge
- [ ] planning
- [ ] learning
- [ ] natural language processing (communication)

##Perception (solved)##

For the purposes of our project, we can pretend that we've been supplied with some advanced technology that handles the difficult tasks of:

- image recognition
- spatial awareness
- positioning

That we have integrated into our robot as a series of 3rd party plugin subsystems.

###Image recognition###

For image recognition we can pretend that we already have a subsystem provided to us that can recognize:

- block types (esp. for "usable blocks" i.e. chests, furnaces, etc.)
- entities (i.e. blocks that are broken or items that have been dropped)
- mobs:
	- neutral
	- hostile
- players

We can assume that our image recognition "system" can also give us advanced details about its observations. Players, for example, can be recognized individually and their name provided to us. Structured data describing the armor or weapons a hostile mob is wearing/wielding can be assumed too.

###Spatial Awareness###

We get a "point cloud" of voxel objects representating the space we're in. Basically we can pretend that we have some kind of advanced [scanning LIDAR](https://www.kickstarter.com/projects/scanse/sweep-scanning-lidar) that can return a representation of the world around us as a set of 3d blocks. It is **so** powerful in fact that it has:

- extreme range
- x-ray type penetration (so that it can see blocks behind blocks)

***NOTE***

    For the purposes of our research, we might want to have an option to "toggle" this
    x-ray vision on or off depending on how much of a challenge we want.

###Positioning###

At all times we have access to a sort of "Super GPS" that can always tell us the absolute position (including facing) of our robot; it works underwater, indoors, and even underground!

##Movement and Manipulation (solved)##

Moving a robot is a huge area of research, even if the means of locomotion is relatively simple i.e. wheels versus bipedal walking.

Manipulation of the physical environment in which the robot is operating is yet another huge area of research and engineering. Evidence of this can be seen in the DARPA challenges where many robots are unable to perform a task as (seemingly) easy as opening a door.

###Movement###

For our purposes, we can assume that we have a system in place that allows us to move our robot reliably (and somewhat safely).

###Manipulation###

Manipulating objects can be considered solved for us. Again, we can assume we have a system provided to us that can accept commands such as "open door" or "activate lever" that when issued to our robot are carried out without any further effort from us.

##Reasoning (unsolved)##

`TODO`

##Knowledge (unsolved)##

`TODO`

##Planning (unsolved)##

`TODO`

##Learning (unsolved)##

`TODO`

##Communication (partial?)##

###Channels###

`TODO`
- imaginary "perfect text messaging network"
- teamspeak? (or equivalent)

###Natural Language Processing (NLP)###

`TODO`
