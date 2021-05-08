import collections
import networkx as nx
import osmnx
import matplotlib.pyplot as plt
import os.path
import pickle

PLACE = 'Barcelona, Catalonia'
IMAGE_FILENAME = 'barcelona.png'
GRAPH_FILENAME = 'barcelona.graph'
SIZE = 800
HIGHWAYS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/1090983a-1c40-4609-8620-14ad49aae3ab/resource/1d6c814c-70ef-4147-aa16-a49ddb952f72/download/transit_relacio_trams.csv'
CONGESTIONS_URL = 'https://opendata-ajuntament.barcelona.cat/data/dataset/8319c2b1-4c21-4962-9acd-6db4c5ff1148/resource/2d456eb5-4ea6-4f68-9794-2f3f1a58a933/download'

Highway = collections.namedtuple('Highway', 'a') # Tram
Congestion = collections.namedtuple('Congestion', 'a')

def exists_graph(filename):
    return os.path.isfile(filename)

def download_graph(place):
    graph = osmnx.graph_from_place(place, network_type='drive', simplify=True)
    #graph = osmnx.utils_graph.get_digraph(graph, weight='length')
    return graph

def save_graph(graph, filename):
    with open(filename, 'wb') as file:
        pickle.dump(graph, file)

def load_graph(filename):
    with open(filename, 'rb') as file:
        graph = pickle.load(file)
    return graph

def plot_graph(graph, save=True):
    if save:
        osmnx.plot_graph(graph, save=True, filepath=IMAGE_FILENAME)
    else:
        osmnx.plot_graph(graph)

def download_csv(url):
    with urllib.request.urlopen(url) as response:
        lines = [l.decode('utf-8') for l in response.readlines()]
    reader = csv.reader(lines, delimiter=',', quotechar='"')
    next(reader)  # ignore first line with description
    for line in reader:
        way_id, description, coordinates = line
        print(way_id, description, coordinates)

def download_highways(url):
    pass

def download_congestions(url):
    pass

def build_igraph():
    pass

def test():
    # load/download graph (using cache) and plot it on the screen
    if not exists_graph(GRAPH_FILENAME):
        graph = download_graph(PLACE)
        save_graph(graph, GRAPH_FILENAME)
        print("Graph generated")
    else:
        graph = load_graph(GRAPH_FILENAME)
        print("Graph loaded")
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

test()