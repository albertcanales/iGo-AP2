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
Location = collections.namedtuple('Location', 'Latitud Longitud')

def exists_graph(filename):
    return os.path.isfile(filename)

def download_graph(place):
    print("Downloading graph...")
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
    edges = ox.graph_to_gdfs(graph, nodes=False)
    edge_types = edges['congestion'].value_counts()
    color_list = ox.plot.get_colors(n=len(edge_types), cmap='plasma_r')
    color_mapper = pd.Series(color_list, index=edge_types.index).to_dict()

    # get the color for each edge based on its highway type
    ec = [color_mapper[d['congestion']] for u, v, k, d in graph.edges(keys=True, data=True)]
    ox.plot_graph(nx.MultiDiGraph(graph), edge_color=ec, node_size=0, save=save, filepath=IMAGE_FILENAME)

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
    print("Downloading highways...")
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
    print("Downloading congestions...")
    with urllib.request.urlopen(url) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
    reader = csv.reader(lines, delimiter='#', quotechar='"')

    congestions = {}
    for line in reader:
        line = list(map(int, line))
        way_id, date, actual, predicted = line
        if way_id not in congestions.keys() or congestions[way_id].date < date:
            congestions[way_id] = Congestion(date, actual, predicted)
    return congestions

def shortest_path(graph, source, target):
    return nx.shortest_path(graph, source=source, target=target, weight='itime')

def get_location(graph, string):
    parts = string.split(" ")
    try:
        x = float(parts[0])
        y = float(parts[1])
        node = ox.nearest_nodes(graph, [x], [y])[0]
        return Location(graph.nodes[node]['x'], graph.nodes[node]['y'])
    except:
        location = ox.geocode(string)
        node = ox.nearest_nodes(graph, location)
        nodeInfo = graph.nodes[node]
        return Location(nodeInfo['x'], nodeInfo['y'])


def get_igraph(graph):
    # Se debe calcular itime con length, maxspeed i congestion. USAR función auxiliar
    for node1 in graph.nodes:
        for node2 in graph.neighbors(node1):
            #print(graph[node1][node2][0])
            try:
                graph[node1][node2]['itime'] = graph[node1][node2]['length'] / float(graph[node1][node2]['maxspeed'])
            except:
                graph[node1][node2]['itime'] = graph[node1][node2]['length'] / 30
            if graph[node1][node2]['congestion'] == 0:
                graph[node1][node2]['itime'] /= 0.7
            elif graph[node1][node2]['congestion'] == 2:
                graph[node1][node2]['itime'] /= 0.8
            elif graph[node1][node2]['congestion'] == 3:
                graph[node1][node2]['itime'] /= 0.6
            elif graph[node1][node2]['congestion'] == 4:
                graph[node1][node2]['itime'] /= 0.4
            elif graph[node1][node2]['congestion'] == 5:
                graph[node1][node2]['itime'] /= 0.2
            elif graph[node1][node2]['congestion'] == 6:
                graph[node1][node2]['itime'] = float('inf')
    return graph # Provisional

def build_igraph(graph, highways, congestions):
    nx.set_edge_attributes(graph, 0, 'congestion')
    # Añadir congestions a las highways

    for key in congestions.keys():
        #coords es la lista de coordenadas de la highway correspondiente
        coords = list(highways[key].coords.coords)
        coordsY = [coords[i][1] for i in range(len(coords))]
        coordsX = [coords[i][0] for i in range(len(coords))]
        nodes = ox.nearest_nodes(graph, coordsX, coordsY)
        for i in range(1,len(nodes)):
            if (nx.has_path(graph, source = nodes[i-1], target = nodes[i])):
                path = nx.shortest_path(graph, source = nodes[i-1], target = nodes[i], weight = 'length')
                #Asignamos las congestiones
                for i in range(1, len(path)):
                    graph[path[i-1]][path[i]]['congestion'] = congestions[key].actual
                    #graph.add_edge(, , congestion = )
    
    # Completar congestion del resto



    # Calcular itime
    igraph = get_igraph(graph)
    return igraph

def main():
    graph = get_graph()
    #plot_graph(graph)

    # download highways and plot them into a PNG image
    highways = download_highways(HIGHWAYS_URL)
    #plot_highways(highways, 'highways.png', SIZE)

    # download congestions and plot them into a PNG image
    congestions = download_congestions(CONGESTIONS_URL)
    #plot_congestions(highways, congestions, 'congestions.png', SIZE)

    # get the 'intelligent graph' version of a graph taking into account the congestions of the highways
    igraph = build_igraph(graph, highways, congestions)

    # get 'intelligent path' between two addresses and plot it into a PNG image
    # ipath = get_shortest_path_with_ispeeds(igraph, "Campus Nord", "Sagrada Família")
    # plot_path(igraph, ipath, SIZE)

def test():
    graph = get_graph()
    highways = download_highways(HIGHWAYS_URL)
    congestions = download_congestions(CONGESTIONS_URL)

    igraph = build_igraph(graph, highways, congestions)

    x = True
    for node1, info1 in igraph.nodes.items():
        if x:
            print(node1, info1)
            # for each adjacent node and its information...
            for node2, edge in igraph.adj[node1].items():
                print('    ', node2)
                print('        ', edge)
            x = False

    #plot_graph(igraph)


main()