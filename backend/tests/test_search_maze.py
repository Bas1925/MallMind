"""BFS and DFS on the NOVA service maze. No database."""

from __future__ import annotations

from app.routing.astar import astar
from app.routing.graph import graph_from_seed
from app.routing.search import bfs, dfs
from app.seed.nova_mall import build_nova_mall


def _maze():
    graph = graph_from_seed(build_nova_mall())
    start = graph.node_by_key("maze-start").id
    goal = graph.node_by_key("maze-goal").id
    return graph, start, goal


def test_bfs_takes_fewer_steps_than_dfs() -> None:
    graph, start, goal = _maze()
    breadth = bfs(graph, start, goal)
    depth = dfs(graph, start, goal)
    shortest = astar(graph, start, goal)

    assert breadth.ok and depth.ok and shortest.ok
    assert len(breadth.node_ids) - 1 == 3
    assert len(depth.node_ids) - 1 == 9
    assert depth.total_distance_m > breadth.total_distance_m
    assert shortest.total_distance_m == breadth.total_distance_m
    assert graph.nodes[depth.node_ids[1]].key == "maze-a1"
    assert graph.nodes[breadth.node_ids[1]].key == "maze-s1"


def test_dfs_enters_both_dead_ends_before_the_goal() -> None:
    graph, start, goal = _maze()
    depth = dfs(graph, start, goal)
    keys = [graph.nodes[node_id].key for node_id in depth.visited_ids]
    goal_at = keys.index("maze-goal")
    assert keys.index("maze-b2") < goal_at
    assert keys.index("maze-d2") < goal_at
    assert "maze-b2" not in [graph.nodes[node_id].key for node_id in depth.node_ids]


def test_bfs_stays_out_of_the_main_mall() -> None:
    graph, start, goal = _maze()
    breadth = bfs(graph, start, goal)
    visited = {graph.nodes[node_id].key for node_id in breadth.visited_ids}
    assert "h-ground-110-10" not in visited
    assert "maze-goal" in visited
