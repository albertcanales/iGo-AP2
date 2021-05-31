![](/images/banner.png)

# iGo-BCN
## By Javier Nistal Salas i Albert Canales Ros

iGo-Bot is a Telegram bot that guides you through Barcelona. The project is composed by two files: `igo.py` and `bot.py`, described on the next sections.

## iGo.py

The file `igo.py` has the purpose of managing the iGraph from Barcelona. At the beggining, it contains some string constants for managing the input and some named tuples with the same purpose.

But most importantly it contains the class iGraph. When initialized, the necessary data for iGraph is downloaded (or loaded from cache if possible) and it is saved on a private attribute.

The API offers the following methods:

-  get_shortest_path(source_loc, target_loc, filename): Given two locations, it finds the optimal path from the first to the second using the `itime`. If given a file name, it will also save an image of the path using it. 

- get_location(string): Given coordinates or a name of a place, it will return the location corresponding to the nearest node from that position.

- plot_graph(save=True): It plots the iGraph using the method from osmnx. If save, it also saves the image.

# TODOs

## igo.py
- ~~No utilitzar os per la lectura, lliçons (Canales)~~
- ~~Utilitzar SIZE, al lliçons està com fer-lo servir~~
- ~~Completar congestions~~
- ~~Limpiar eurística para itime~~
- ~~Tener en cuenta ángulos y esas cosas~~
- ~~Separar graph en una clase~~
- ~~Métodos que no requieran un graph~~
- ~~Comentar código, elecciones de diseño~~
- ~~Que actualice valores cada 5 min~~
- ~~Traducir comentarios~~
- ~~Geocoder no funciona bien, siempre devuelve lo mismo a los nombres~~
- ~~Que no peti si no hi ha internet~~
- Que la foto de staticmaps es generi a igo, funció per eliminar fotos
- Icones mapa

## bot.py
- ~~Posar bonica output (treure interacció?)~~
- ~~Mètode go (requereix coses abans)~~
- ~~Fer StaticMap a pos~~
- ~~Fer que les locations vagin amb l'usuari, no que sigui global~~
- ~~Treure boto request (reiniciar conversa?)~~
- ~~Canviar nom/foto bot~~
- ~~Treure globals a igraph?~~
- ~~Provar que li arribi més d'una connexió~~
- ~~Avisar quan estigui actualitzant congestions~~

## General
- Documentar codi
- Diferenciar mètodes publics/privats API
- Seguir regles PEP (0 DIRECTE!!!)
- Fer README amb documentació

