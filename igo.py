import collections
import networkx as nx
import osmnx as ox
import pandas as pd
import os.path
import pickle
import csv
import urllib
from shapely.geometry import LineString
import threading
import time

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
        '''The class constructor'''
        graph = self.get_graph()
        #plot_graph(graph)

        # download highways and parse them accordingly
        highwayscoords = self._download_highways(HIGHWAYS_URL)

        print("Proyecting highways...")
        self._highways = {}
        for key in highwayscoords.keys():
            coords = list(highwayscoords[key].coords.coords)
            coordsY = [coords[i][1] for i in range(len(coords))]
            coordsX = [coords[i][0] for i in range(len(coords))]
            nodes = ox.get_nearest_nodes(graph, coordsX, coordsY)
            self._highways[key] = nodes

        #plot_highways(highways, 'highways.png', SIZE)

        # download congestions and parse them accordingly
        self._congestions = self._download_congestions(CONGESTIONS_URL)

        # get the 'intelligent graph' version of a graph taking into account the congestions of the highways
        self._igraph = self._build_igraph(graph, self._highways, self._congestions)

        # update igraph every 5 minutes
        self._update_igraph()

    def get_shortest_path(self, source_loc, target_loc):
        '''
        Computes the shortest path between the two specified locations
        Params:
            - source_loc: A location with the source of the path
            - target_loc: A location with the target of the path
        Returns a list of locations along the resulting path, if there is no path None is returned.
        '''
        source = ox.get_nearest_nodes(self.igraph, [source_loc.lat], [source_loc.lon])[0]
        target = ox.get_nearest_nodes(self.igraph, [target_loc.lat], [target_loc.lon])[0]
        if nx.has_path(self.igraph, source=source, target=target):
            node_path = nx.shortest_path(self._igraph, source=source, target=target, weight='itime')
            return self._get_path_coords(node_path)
        return None

    def get_location(self, string):
        '''
        Gets the locationo of the node associated with the given string.
        Params:
            - string: A string that can either be the name of a location or two space separated decimal numbers representing the coordinates.
        Returns the resulting location.
        '''
        if string is not None:
            parts = string.split(" ")
            try:
                x = float(parts[0])
                y = float(parts[1])
                node = ox.get_nearest_nodes(self._igraph, [x], [y])[0]
                return Location(self._igraph.nodes[node]['x'], self._igraph.nodes[node]['y'])
            except:
                location = ox.geocode(string)
                node = ox.get_nearest_nodes(self._igraph, [location[1]], [location[0]])[0]
                node_info = self._igraph.nodes[node]
                return Location(node_info['x'], node_info['y'])

    def get_graph(self):
        '''
        Gets the graph of the streets from cache or downloads it from the internet if necessary.
        Returns the obtained graph.
        '''
        # load/download graph (using cache) and plot it on the screen
        if not self._exists_graph(GRAPH_FILENAME):
            graph = self._download_graph(PLACE)
            self._save_graph(graph, GRAPH_FILENAME)
            print("Graph generated")
        else:
            graph = self._load_graph(GRAPH_FILENAME)
            print("Graph loaded")
        return graph

    def plot_graph(self, graph, attr=None, save=True):
        '''
        Plots the given graph.
        Params:
            - graph: The graph to plot.
            - attr = None: The name of the attribute the color should depends on.
            - save = True: A boolean that determines whether the resulting image should be saved.
        This function does not return anything.
        '''
        multiGraph = nx.MultiDiGraph(graph)

        if attr is None:
            ox.plot_graph(multiGraph, node_size=0, save=save, filepath=IMAGE_FILENAME)
        else:
            edges = ox.graph_to_gdfs(multiGraph, nodes=False)
            # assigns a different color for each value of atribute attr
            edge_types = edges[attr].value_counts()
            color_list = ox.plot.get_colors(n=len(edge_types), cmap='plasma_r')
            color_mapper = pd.Series(color_list, index=edge_types.index).to_dict()

            # get the color for each edge based on its attr
            ec = [color_mapper[d[attr]] for u, v, k, d in multiGraph.edges(keys=True, data=True)]
            ox.plot_graph(multiGraph, edge_color=ec, node_size=0, save=save, filepath=IMAGE_FILENAME)
    
    # Functions for input / output

    def _exists_graph(self, filename):
        '''
        Determines whether the graph of the city is stored in cache.
        Params:
            - Filename: A string with the name the file with the graph should have.
        Returns a boolean with the result.
        '''
        return os.path.isfile(filename)

    def _download_graph(self, place):
        '''
        Downloads the graph of the streets from the specified place.
        Params:
            - Place: A string specifying the route the graph should be downloaded from
        Returns the obtained graph.
        '''
        print("Downloading graph...")
        graph = ox.graph_from_place(place, network_type='drive', simplify=True)
        graph = ox.utils_graph.get_digraph(graph, weight='length')
        return graph

    def _save_graph(self, graph, filename):
        '''
        Saves the graph in cache so it won't have to be downloaded again.
        Params:
            - graph: The graph to be saved.
            - filename: A string with the name of the file that will store the graph.
        This function does not return anything.
        '''
        with open(filename, 'wb') as file:
            pickle.dump(graph, file)

    def _load_graph(self, filename):
        '''
        Loads the graph of the streets from cache.
        Params:
            - filename: The name of the file the graph should be extracted from.
        Returns the obtained graph.
        '''
        with open(filename, 'rb') as file:
            graph = pickle.load(file)
        return graph

    def _get_line_string_from_coords(self, coords):
        '''
        Converts a string with coordinates separated by comas to linestring.
        Params:
            - coords: A string containing the aforementioned coma separated coordinates.
        Returns the resulting linestring.
        '''
        coords = coords.split(",")
        coords = [(float(coords[i]), float(coords[i+1])) for i in range(0,len(coords),2)]
        return LineString(coords)

    def _download_highways(self, url):
        '''
        Downloads the highways from the specified url.
        Params:
            - url: A string containing the url the highways should be downloaded from.
        Returns a dictionary mapping the ids to the obtained highways.
        '''
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
        '''
        Downloads the congestions from the specified url.
        Params:
            - url: A string containing the url the congestions should be downloaded from.
        Returns a dictionary mapping the ids to the obtained congestions.
        '''
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

    def _get_speed(self, speeds):
        '''
        Parses the given speeds to a single number.
        Params:
            - speeds: It can either be a list of numbers represented as strings or a single number reprented as a string.
        Returns the average of the given numbers.
        '''
        if isinstance(speeds,list):
            return sum(list(map(int, speeds))) / len(speeds)
        else:
            return int(speeds)

    def _get_path_coords(self, path):
        coords_path = []
        for node in path:
            node_info = self._igraph.nodes[node]
            coords_path.append(Location(node_info['x'], node_info['y']))
        return coords_path

    # Functions for building the iGraph

    def _update_igraph(self):
        '''
        Every 5 minutes updates the igraph to match the available data about congestions.
        This function does not finish so it does not return anything.
        '''
        threading.Timer(300, self._update_igraph).start()
        print("Updating...")

        oldCongestions = self._congestions
        highways = self._highways
        congestions = self._download_congestions(CONGESTIONS_URL)
        graph = self._igraph

        anyUpdate = False
        for key in congestions.keys():
            #If nothing has changed there is nothing to update
            if congestions[key].actual != oldCongestions[key].actual:
                #Nodes is the list of nodes of the corresponding highway
                nodes = self._highways[key]
                for i in range(1,len(nodes)):
                    #For each segment of the highway assign the congestion to the shortest path between the nodes that it connects.
                    if (nx.has_path(graph, source = nodes[i-1], target = nodes[i])):
                        #Path is the aforementioned shortest path.
                        path = nx.shortest_path(graph, source = nodes[i-1], target = nodes[i], weight = 'length')
                        for i in range(1, len(path)):
                            graph[path[i-1]][path[i]]['congestion'] = congestions[key].actual
                            graph[path[i-1]][path[i]]['congestionInfo'] = (congestions[key].actual > 0)
                            anyUpdate = True

        #If there has been an update the estimations and the itime need to be recomputed
        if anyUpdate:
            #Reset the previous estimations to "No data"
            for node1, info1 in graph.nodes.items():
                for u, v, data in graph.in_edges(node1, data = True):
                    if not data['congestionInfo']:
                        graph[u][v]['congestion'] = 0

            #Recompute estimation
            for iteration in range(6):
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

            #Recompute iTimes
            self._igraph = self._get_igraph(graph)
            print("Done")


    def _get_igraph(self, graph):
        '''
        Given a graph with complete congestion data computes the itimes values.
        Params:
            - graph: The graph of the streets with complete congestions values.
        Returns the resulting igraph.
        '''
        for node1 in graph.nodes:
            for node2 in graph.neighbors(node1):
                if ('maxspeed' in graph[node1][node2]):
                    #If there is data about the max speed we can assign the time it would take to get to the end of the street.
                    graph[node1][node2]['itime'] = graph[node1][node2]['length'] / self._get_speed(graph[node1][node2]['maxspeed'])
                else:
                    #If there is no data about the max speed then 30 km/h is a decent guess.
                    graph[node1][node2]['itime'] = graph[node1][node2]['length'] / 30

                if graph[node1][node2]['congestion'] == 6:
                    #If the street is blocked we can't use it.
                    graph[node1][node2]['itime'] = float('inf')
                else:
                    #We need to increase the travel time if there is congestion.
                    graph[node1][node2]['itime'] /= 1-(graph[node1][node2]['congestion']-1)/6

                #It takes some extra seconds to change streets (One must usually turn, cross an intersection or wait for the traffic light).
                graph[node1][node2]['itime'] += 5
        return graph

    def _build_igraph(self, graph, highways, congestions):
        '''
        Builds the igraph from the graph of the streets, the highways and the congestion data available.
        Params:
            - graph: The graph of the streets.
            - highways: A dictionary that maps the ids with the highways.
            - congestions: A dictionary that maps the ids with the congestions.
        Returns the resulting igraph.
        '''
        print("Building iGraph...")

        #Initialize the congestion to "No data"
        nx.set_edge_attributes(graph, 0, 'congestion')
        nx.set_edge_attributes(graph, False, 'congestionInfo')

        #Assign the congestion data we do have
        for key in congestions.keys():
            #If our data about the congestion is just "No data" it's useless.
            if congestions[key].actual > 0:
                #nodes is the list of nodes of the corresponding highway
                nodes = highways[key]

                for i in range(1,len(nodes)):
                    #For each segment of the highway assign the congestion to the shortest path between the nodes that it connects.
                    if (nx.has_path(graph, source = nodes[i-1], target = nodes[i])):
                        #Path is the aforementioned shortest path.
                        path = nx.shortest_path(graph, source = nodes[i-1], target = nodes[i], weight = 'length')
                        for i in range(1, len(path)):
                            graph[path[i-1]][path[i]]['congestion'] = congestions[key].actual
                            graph[path[i-1]][path[i]]['congestionInfo'] = True


        print("Filling congestions...")

        # Complete the remaining congestions
        # For each iteration for each node extend the average congestion of the adjacent
        # streets with known congestion to the adjacent streets with unknown congestion.
        for iteration in range(6):
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

        # The remaining streets are very isolated so we can assume there won't be many people using them.
        for node1, info1 in graph.nodes.items():
            for u, v, data in graph.in_edges(node1, data = True):
                if data['congestion'] == 0:
                    graph[u][v]['congestion'] = 1

        print("Declaring iTimes...")

        # Compute the itime of every street
        igraph = self._get_igraph(graph)
        
        print("Done")


        return igraph