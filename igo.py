import collections
import networkx as nx
import osmnx as ox
import pandas as pd
import os.path
import pickle
import csv
import urllib
from shapely.geometry import LineString

PLACE = 'Barcelona, Catalonia'
IMAGE_FILENAME = 'barcelona.png'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

Highway = collections.namedtuple('Highway', 'description coords')
Congestion = collections.namedtuple('Congestion', 'date actual predicted')
Highwestion = collections.namedtuple('Highwestion', 'description coords actualCongestion predictedCongestion')

def exists_graph(filename):
    return os.path.isfile(filename)

def download_graph(place):
    graph = ox.graph_from_place(place, network_type='drive', simplify=True)
    graph = ox.utils_graph.get_digraph(graph, weight='length')
    return graph

def save_graph(graph, filename):
    with open(filename, 'wb') as file:
        pickle.dump(graph, file)

def load_graph(filename):
    with open(filename, 'rb') as file:
        graph = pickle.load(file)
    return graph

def plot_graph(graph, save=True):
    ox.plot_graph(graph, save=save, filepath=IMAGE_FILENAME)

def get_graph():
    # load/download graph (using cache) and plot it on the screen
    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)
        print("Graph generated")
    else:
        graph = load_graph(GRAPH_FILENAME)
        print("Graph loaded")
    return graph

def get_line_string_from_coords(coords):
    coords = coords.split(",")
    coords = [(float(coords[i]), float(coords[i+1])) for i in range(0,len(coords),2)]
    return LineString(coords)

def download_highways(url):
    with urllib.request.urlopen(url) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
    reader = csv.reader(lines, delimiter=',', quotechar='"')
    next(reader)  # ignore first line with description

    highways = {}
    for line in reader:
        way_id, description, coordinates = line
        highways[int(way_id)] = Highway(description, get_line_string_from_coords(coordinates))
    return highways

def download_congestions(url):
    with urllib.request.urlopen(url) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
    reader = csv.reader(lines, delimiter='#', quotechar='"')
    next(reader)  # ignore first line with description

    congestions = {}
    for line in reader:
        line = list(map(int, line))
        way_id, date, actual, predicted = line
        if way_id not in congestions.keys() or congestions[way_id].date < date:
            congestions[way_id] = Congestion(date, actual, predicted)
    return congestions


def get_igraph(graph):
    # Se debe calcular itime con length, maxspeed i congestion. USAR función auxiliar
    return graph # Provisional

def build_igraph(graph, highways, congestions):
    # Añadir congestions a las highways
    highwestions = {}
    for it in highways.keys():
        if congestions.get(it) is not None:
            highwestions[it] = Highwestion(highways[it].description, highways[it].coords, congestions[it].actual, congestions[it].predicted)
        else:
            highwestions[it] = Highwestion(highways[it].description, highways[it].coords, 'Unknown', 'Unknown')
    # Añadir highways a graph
    for key in congestions.keys():
    	coords = list(highways[key].coords.coords)
    	start = coords[0]
    	end = coords[-1]
    	bestStart = 0
    	bestStartDistSqr = 10000000000
    	bestEnd = 0
    	bestEndDistSqr = 10000000000

    	for node, info in graph.nodes.items():
    		startDistSqr = (info['x']-start[0])**2 + (info['y']-start[1])**2
    		if startDistSqr < bestStartDistSqr:
    			bestStartDistSqr = startDistSqr
    			bestStart = node
    		endDistSqr = (info['x']-end[0])**2 + (info['y']-end[1])**2
    		if endDistSqr < bestEndDistSqr:
    			bestEndDistSqr = endDistSqr
    			bestEnd = node

    	#print('from', bestStart, 'to', bestEnd)
    	#path = nx.shortest_path(graph, source = bestStart, target = bestEnd, weight = 'length')
    	#print(type(path))
    

    # Completar congestion del resto

    # Calcular itime
    igraph = get_igraph(graph)
    return igraph

def main():
    graph = get_graph()
    plot_graph(graph)

    # download highways and plot them into a PNG image
    highways = download_highways(HIGHWAYS_URL)
    plot_highways(highways, 'highways.png', SIZE)

    # download congestions and plot them into a PNG image
    congestions = download_congestions(CONGESTIONS_URL)
    plot_congestions(highways, congestions, 'congestions.png', SIZE)

    # get the 'intelligent graph' version of a graph taking into account the congestions of the highways
    igraph = build_igraph(graph, highways, congestions)

    # get 'intelligent path' between two addresses and plot it into a PNG image
    ipath = get_shortest_path_with_ispeeds(igraph, "Campus Nord", "Sagrada Família")
    plot_path(igraph, ipath, SIZE)

def test():
    graph = get_graph()
    x = True
    for node1, info1 in graph.nodes.items():
        if x:
            print(node1, info1)
            # for each adjacent node and its information...
            for node2, edge in graph.adj[node1].items():
                print('    ', node2)
                print('        ', edge)
            x = False
    highways = download_highways(HIGHWAYS_URL)
    y = 10
    print(type(highways))
    for it in highways:
        if y > 0:
            print(type(it))
            print(print(highways[it].coords))
            y -= 1
    congestions = download_congestions(CONGESTIONS_URL)
    y = 10
    print(type(congestions))
    for it in congestions:
        if y > 0:
            print(type(it))
            print(it, congestions[it])
            y -= 1

    igraph = build_igraph(graph, highways, congestions)


test()