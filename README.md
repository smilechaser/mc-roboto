***STATUS:*** Archived. I don't intend to develop this project any further.

# mc-roboto

A MineCraft client library with dynamic protocol capability for building an
Autonomous Agent (robot).

**Status**: *Alpha* (experimental)

![screenshot](screenshot.png)

## Motivation
I've always wanted to make a robot. But why a MineCraft one? There are several reasons:

1. cost
2. accessible
3. meaningful

There are other advantages in using MineCraft as a platform as it allows us to consider some [AI Goals](./research/AI_goals.md) as effectively solved - at least for the purposes of our research.

### Cost

I remember reading an article (can't find it now) about some researcher
integrating MineCraft with a robotics framework (ROS?). They mentioned
something about that effectively meaning that anyone could have their own robot
for the cost of a MineCraft game. So, in essence, anyone could have their own
personal robot for around $30 USD. Can't beat that right?

### Accessible

Because of the market penetration of the game there are potentially millions of
players who could experience "robotics" through this project. Given the
adoption of MineCraft in educational settings, there is the potential for kids
to have "grown up with" these kind of robots.

This, in turn, casts a wide net over the hearts and minds of people who can not
only help further Artificial Intelligence but are wise enough to make social
and political choices about its use.

### Meaningful

Everyone who has played the game understands what constitutes a "good" player.
If this robot progresses to the point of becoming as good (or better) than
human players then that is effectively passing a Turing Test. Right? 😀

Seriously though. Imagine having a robot companion in the game that can help
you gather resources. Or build. Or explore. What about rescuing you? That might
sound amusing at first, but consider this quote:

	“If I were a large company with deep pockets, I would accept that robotics is
	what is called a ‘formative’ market and just like shopping on the web, it will
	take a decade or so to ramp up. Robots are innovations that do not directly
	replace people and thus it is hard for people to imagine how to use them—thus
	the market is formative. The theory of diffusion of innovation indicates that
	potential end-users, not developers, need to experiment with applications to
	see what works (and not just physically but human-robot interaction as well).

	However, robots have to be extremely reliable and the software customizable
	enough to allow the end-users to tinker and adapt the robots, so that the
	end-user can find the ‘killer app.’ Essentially, you can crowdsource the task
	of finding the best, most profitable uses of robots, but only if you have good
	enough robots that can be reconfigure easily and the software is open enough. I
	would concentrate on creating generic ground, aerial, and marine robots with
	customizable software and user interfaces in order to enable their regular
	employees (and customers) to figure out the best uses.

	In order to make sure the development was pushing towards the most reliable,
	reconfigurable, and open robots possible, I suggest the developers focus on the
	emergency response domain. Disasters are the most demanding application and
	come in so many variations that it is a constant test of technology and users.
	Imagine the wealth of ideas and feedback from fire rescue teams, the Coast
	Guard, and the American Red Cross, just to name a few! Focusing on emergency
	management would also have a positive societal benefit.”

That's a quote from this [article](http://spectrum.ieee.org/automaton/robotics/robotics-hardware/what-google-should-do-with-its-robots)
which, well, really sums up what this project is aiming to do.

Maybe having a robot that is capable of bringing you porkchops and torches when
you've fallen into a mineshaft might just save your (IRL) life some day. 🤔

## Features

 - dynamic protocol - can switch to use the protocol version you specify at runtime (uses data from the [PrismarineJS minecraft-data project](https://github.com/PrismarineJS/minecraft-data.git))
 - handles compression
 - event-driven framework

## Limitations

- does not (currently) handle online mode (aka encryption)
- example robot is really, *really* simple 😉

## Platform

- python3
- OS X [*1*]

[*1*] This is what I develop and test on. It *might* work on other systems...but your mileage may vary.

## Requirements

* minecraft-data (linked submodule)
* virtualenv

## Installation

1. clone this repo
1. create a virtualenv and activate it:
	1. `virtualenv venv`
	1. `source venv/bin/activate`
1. install the dependencies:
	1. `pip install -r requirements.txt`

## Usage

There are a couple of hard-coded defaults that you may wish to change:

- server: *localhost*
- port: *25565* (default MineCraft server port)
- robot name: *bobo*

These can be searched for and changed in main.py if so desired.

To run the program:

1. `python main.py`
2. the program should launch, connect to the server, and spawn your robot player into the world
3. you can then chat with your robot, using the /tell [*robot name*] command:
	- i.e. `/tell bobo goto ~ ~ ~1`

## Contributing

Want to help? Awesome! There are a couple of ways you can help out:

1. Testing
2. Research
3. Code

### Testing

Install the project and take it for a spin. Find what's broken and enter an
issue describing what you found.

And, more importantly, think about ways of testing this thing. Right now the
"unit test" coverage is non-existent. 😔 Contributions to that are always
welcome. But also - how do we test the robot's abilities and behavior at a
higher level? Thoughts?

### Research

I am NOT an A.I. expert by any stretch of the imagination. I have a few ideas
and things I'd like to try, but this is a complicated field. So take a look in
the [research](./research) folder and add your ideas!

### Code

Are you a programmer? Cool! Grab an open issue and fix it but make sure you
check out the [contributor's guide](./.github/CONTRIBUTING.md) first.
