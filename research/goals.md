#Goals#

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

##Perception##

For the purposes of our project, we can pretend that we've been supplied with some advanced technology that handles the difficult tasks of:

- image recognition
- spatial awareness
- positioning

That we have integrated into our robot as a series of 3rd party plugin subsystems.

###Image recognition###

`TODO`
Entities, block types, mobs (hostile, neutral, or friendly), players

###Spatial Awareness###

We get a "point cloud" of voxel objects representating the space we're in. Basically we can pretend that we have some kind of advanced [scanning LIDAR](https://www.kickstarter.com/projects/scanse/sweep-scanning-lidar) that can return a representation of the world around us as a set of 3d blocks. It is **so** powerful in fact that it has:

- extreme range
- x-ray type penetration (so that it can see blocks behind blocks)

***NOTE***

    For the purposes of our research, we might want to have an option to "toggle" this
    x-ray vision on or off depending on how much of a challenge we want.

###Positioning###

At all times we have access to a sort of "Super GPS" that can always tell us the absolute position (including facing) of our robot; it works underwater, indoors, and even underground!

##Movement and Manipulation##

###Movement###

`TODO`

###Manipulation###

`TODO`


##Reasoning##

`TODO`

##Knowledge##

`TODO`

##Planning##

`TODO`

##Learning##

`TODO`

##Natural Language Processing (NLP)##

`TODO`
