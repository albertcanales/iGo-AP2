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
Location = collections.namedtuple('Location', 'lat lon')

class iGraph:

    def __init__(self):
        graph = self.get_graph()
        #plot_graph(graph)

        # download highways and plot them into a PNG image
        highways = self._download_highways(HIGHWAYS_URL)
        #plot_highways(highways, 'highways.png', SIZE)

        # download congestions and plot them into a PNG image
        congestions = self._download_congestions(CONGESTIONS_URL)
        #plot_congestions(highways, congestions, 'congestions.png', SIZE)

        # get the 'intelligent graph' version of a graph taking into account the congestions of the highways
        self.igraph = self._build_igraph(graph, highways, congestions)

        # get 'intelligent path' between two addresses and plot it into a PNG image
        # ipath = get_shortest_path_with_ispeeds(igraph, "Campus Nord", "Sagrada Família")
        # plot_path(igraph, ipath, SIZE)

    def shortest_path(self, source, target):
        if nx.has_path(graph, source=source, tryarget=target):
            return nx.shortest_path(graph, source=source, target=target, weight='itime')
        return None

    def get_location(self, string):
        parts = string.split(" ")
        try:
            x = float(parts[0])
            y = float(parts[1])
            node = ox.nearest_nodes(self.igraph, [x], [y])[0]
            return Location(self.igraph.nodes[node]['x'], self.igraph.nodes[node]['y'])
        except:
            location = ox.geocode(string)
            node = ox.nearest_nodes(self.igraph, location[0], location[1])
            nodeInfo = self.igraph.nodes[node]
            return Location(nodeInfo['x'], nodeInfo['y'])

    def get_graph(self):
        # load/download graph (using cache) and plot it on the screen
        if not self._exists_graph(GRAPH_FILENAME):
            graph = self.download_graph(PLACE)
            self._save_graph(graph, GRAPH_FILENAME)
            print("Graph generated")
        else:
            graph = self._load_graph(GRAPH_FILENAME)
            print("Graph loaded")
        return graph

    def plot_graph(self, graph, save=True):
        multiGraph = nx.MultiDiGraph(graph)

        edges = ox.graph_to_gdfs(multiGraph, nodes=False)
        edge_types = edges['congestion'].value_counts()
        color_list = ox.plot.get_colors(n=len(edge_types), cmap='plasma_r')
        color_mapper = pd.Series(color_list, index=edge_types.index).to_dict()

        # get the color for each edge based on its highway type
        ec = [color_mapper[d['congestion']] for u, v, k, d in multiGraph.edges(keys=True, data=True)]
        ox.plot_graph(multiGraph, edge_color=ec, node_size=0, save=save, filepath=IMAGE_FILENAME)

    # Functions for getting input

    def _exists_graph(self, filename):
        return os.path.isfile(filename)

    def _download_graph(self, place):
        print("Downloading graph...")
        graph = ox.graph_from_place(place, network_type='drive', simplify=True)
        graph = ox.utils_graph.get_digraph(graph, weight='length')
        return graph

    def _save_graph(self, graph, filename):
        with open(filename, 'wb') as file:
            pickle.dump(graph, file)

    def _load_graph(self, filename):
        with open(filename, 'rb') as file:
            graph = pickle.load(file)
        return graph

    def _get_line_string_from_coords(self, coords):
        coords = coords.split(",")
        coords = [(float(coords[i]), float(coords[i+1])) for i in range(0,len(coords),2)]
        return LineString(coords)

    def _download_highways(self, url):
        print("Downloading highways...")
        with urllib.request.urlopen(url) as response:
            lines = [l.decode('utf-8') for l in response.readlines()]
        reader = csv.reader(lines, delimiter=',', quotechar='"')
        next(reader)  # ignore first line with description

        highways = {}
        for line in reader:
            way_id, description, coordinates = line
            highways[int(way_id)] = Highway(description, self._get_line_string_from_coords(coordinates))
        return highways

    def _download_congestions(self, url):
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

    # Functions for building the iGraph

    def _get_igraph(self, graph):
        # Se debe calcular itime con length, maxspeed i congestion. USAR función auxiliar
        for node1 in graph.nodes:
            for node2 in graph.neighbors(node1):
                #print(graph[node1][node2][0])
                try:
                    graph[node1][node2]['itime'] = graph[node1][node2]['length'] / float(graph[node1][node2]['maxspeed'])
                except:
                    graph[node1][node2]['itime'] = graph[node1][node2]['length'] / 30
                if graph[node1][node2]['congestion'] == 0:
                    graph[node1][node2]['itime'] = float('inf')
                elif graph[node1][node2]['congestion'] >= 5.99:
                    graph[node1][node2]['itime'] = float('inf')
                else:
                    graph[node1][node2]['itime'] /= 1-(graph[node1][node2]['congestion']-1)/6
        return graph # Provisional

    def _build_igraph(self, graph, highways, congestions):
        print("Building iGraph...")
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
        for iteration in range(10):
            for node1, info1 in graph.nodes.items():
                congestionSum = 0
                congestionCount = 0
                for u, v, data in graph.in_edges(node1, data = True):
                    if data['congestion'] > 0:
                        congestionSum += data['congestion']
                        congestionCount += 1
                for u, v, data in graph.out_edges(node1, data = True):
                    if data['congestion'] > 0:
                        congestionSum += data['congestion']
                        congestionCount += 1
                if congestionCount > 0:
                    averageCongestion = congestionSum//congestionCount
                    for u, v, data in graph.in_edges(node1, data = True):
                        if data['congestion'] == 0:
                            graph[u][v]['congestion'] = max(1, averageCongestion-1)
                    for u, v, data in graph.out_edges(node1, data = True):
                        if data['congestion'] == 0:
                            graph[u][v]['congestion'] = max(1, averageCongestion)

        for node1, info1 in graph.nodes.items():
            for u, v, data in graph.in_edges(node1, data = True):
                if data['congestion'] == 0:
                    graph[u][v]['congestion'] = 1

        igraph = self._get_igraph(graph)
        
        return igraph