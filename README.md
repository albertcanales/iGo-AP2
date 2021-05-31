![](/images/banner.png)

# iGo-BCN
## By Javier Nistal Salas i Albert Canales Ros

iGo-Bot is a Telegram bot that guides you through Barcelona. The project is composed by two files: `igo.py` and `bot.py`, described in the next sections.

## iGo.py

The file `igo.py` has the purpose of managing the iGraph from Barcelona. At the beginning, it contains some string constants for managing the input and some named tuples with the same purpose.

But most importantly, it contains the class iGraph. When initialized, the necessary data for iGraph is downloaded (or loaded from cache if possible) and it is saved in a private attribute. The constructor calls the necessary private functions to compute and keep updated the `itime` attribute. Every 5 minutes it checks for updated congestion data on the web, it does so in a separate thread so as not to lag the bot. The missing congestions are estimated by extending the average of the known congestions of the edges of a node to the unknown congestions of the edges of that node, this process is repeated 6 times and the rest of the streets are assumed to be very remote, this means they probably have fluid traffic.

The API offers the following methods:

-  get_shortest_path(source_loc, target_loc, filename): Given two locations, it finds the optimal path from the first to the second using the `itime`. If given a file name, it will also save an image of the path using it. 

- get_location(string): Given coordinates or a name of a place, it will return the location corresponding to the nearest node from that position.

- plot_graph(save=True): It plots the iGraph using the method from osmnx. If save, it also saves the image.

# TODOs

## General
- ~~Documentar codi~~
- ~~Diferenciar mètodes publics/privats API~~
- ~~Seguir regles PEP (0 DIRECTE!!!)~~
- Fer README amb documentació
- Fer requirements.txt

