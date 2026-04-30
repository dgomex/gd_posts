"""LangGraph wiring for the writer/judge loop.

::

    writer ──► judge ──► [approve|give_up] ──► finalize ──► END
                  │
                  └── [rewrite] ──► writer
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .config import Settings
from .llm import make_llm
from .nodes import decide_next, finalize_node, make_judge_node, make_writer_node
from .state import PostState


def build_graph(settings: Settings) -> CompiledStateGraph:
    """Compile and return the writer/judge LangGraph application."""
    writer_llm = make_llm(settings.writer)
    judge_llm = make_llm(settings.judge)

    writer = make_writer_node(writer_llm, settings.prompts_dir)
    judge = make_judge_node(judge_llm, settings.prompts_dir)

    graph = StateGraph(PostState)
    graph.add_node("writer", writer)
    graph.add_node("judge", judge)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("writer")
    graph.add_edge("writer", "judge")
    graph.add_conditional_edges(
        "judge",
        decide_next,
        {
            "approve": "finalize",
            "give_up": "finalize",
            "rewrite": "writer",
        },
    )
    graph.add_edge("finalize", END)

    return graph.compile()
