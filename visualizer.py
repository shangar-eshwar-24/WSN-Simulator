import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

def plot_network(sim):
    fig, ax = plt.subplots(figsize=(7, 7))
    pos = {i: data['pos'] for i, data in sim.nodes.items()}
    alive = [i for i, d in sim.nodes.items() if d['alive']]
    dead  = [i for i, d in sim.nodes.items() if not d['alive']]

    nx.draw_networkx_edges(sim.graph, pos, ax=ax, alpha=0.3, edge_color='gray')
    nx.draw_networkx_nodes(sim.graph, pos, nodelist=alive, ax=ax, node_color='steelblue', node_size=80)
    nx.draw_networkx_nodes(sim.graph, pos, nodelist=dead,  ax=ax, node_color='red',      node_size=80)
    ax.scatter(*sim.base_station, marker='*', s=300, color='gold', zorder=5, label='Base Station')
    ax.legend(handles=[
        mpatches.Patch(color='steelblue', label='Alive'),
        mpatches.Patch(color='red',       label='Dead'),
    ])
    ax.set_title("WSN Node Map")
    ax.set_xlim(0, sim.area); ax.set_ylim(0, sim.area)
    return fig

def plot_metrics(history):
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    metrics = ['PDR', 'Avg Delay (s)', 'Throughput (pkts)', 'Alive Nodes']
    for ax, key in zip(axes.flat, metrics):
        ax.plot([r[key] for r in history], marker='o', linewidth=1.5)
        ax.set_title(key); ax.set_xlabel("Round"); ax.grid(True)
    plt.tight_layout()
    return fig