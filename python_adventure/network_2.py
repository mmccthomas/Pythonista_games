import networkx as nx
import matplotlib.pyplot as plt
import random
import adventure
import numpy as np
from collections import defaultdict
def shorten(data):
   text = data.short_description
   if text == '' and 'DEAD END' in data.long_description:
        text = 'DEAD END'
   if text == '' and 'MAZE' in data.long_description:
        text = 'MAZE'
   prefixes = ["YOU'RE AT ", "YOU'RE IN ", "YOU'RE ON", "YOU'RE "]
   
   for prefix in prefixes:
      if prefix in text:
       text = text[len(prefix):]
       text = text.strip().rstrip('.')
       break
   return text  

game = adventure.play(loadonly=True)
nodes = {room_no:room_no // 10 for room_no in game.rooms}
edges = []
for room_no, room in game.rooms.items():    
    for t in room.travel_table:
        if hasattr(t.action, 'n'):
            edges.append((room_no, t.action.n))
edges = [edge for edge in edges if edge[0] in nodes and edge[1] in nodes]

G = nx.DiGraph()
for node, layer in nodes.items():
    G.add_node(node, layer=layer)
G.add_edges_from(edges)
cr= '\n'
labels = {room: f'{room}{cr}{shorten(data).lower()}' for room, data in game.rooms.items()}
 
 
k_value = 1 / np.sqrt(len(nodes))
k_value = k_value * 5

# Only show nodes in the 1 to 50 range (Surface and Entrance)
filtered_nodes = [n for n in G.nodes if n in [61, 107, 112, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 98]]
subgraph = G.subgraph(filtered_nodes)

# Calculate the node positions using the Fruchterman-Reingold layout
pos = nx.spring_layout(subgraph, k=k_value, iterations=50, seed=107,scale=10)

plt.close()
plt.figure(figsize=(14, 14))

# nx.draw_networkx_nodes(G, pos, node_size=1200, node_shape='s', node_color='lightblue', edgecolors='black')
# nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowstyle='->', arrowsize=10, width=1.5)
# nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_weight='bold')
# Then use 'subgraph' for your layout and drawing:
pos = nx.spring_layout(subgraph, k=k_value, seed=107)
nx.draw(subgraph, pos, labels={n: labels[n] for n in filtered_nodes})
plt.title('Colossal caves network')
plt.axis('off')
plt.show()



#for room, data in game.rooms.items():
# print(f'{room} {data.long_description} ')
# print(f'{room} {shorten(data)} ')
