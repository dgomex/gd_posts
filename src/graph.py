"""LangGraph wiring for the researcher/writer/judge loop.

::

    researcher ──► writer ──► judge ──► [approve|give_up] ──► finalize ──► END
                       │
                       └────── [rewrite] ────► writer
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .config import Settings
from .llm import make_llm
from .nodes import decide_next, finalize_node, make_judge_node, make_writer_node
from .researcher import DeepResearcher, make_researcher_node
from .state import PostState


def build_graph(settings: Settings) -> CompiledStateGraph:
    """Compile and return the researcher/writer/judge LangGraph application."""
    writer_llm = make_llm(settings.writer)
    judge_llm = make_llm(settings.judge)
    researcher = DeepResearcher(settings.research)

    researcher_node = make_researcher_node(researcher, settings.prompts_dir)
    writer = make_writer_node(writer_llm, settings.prompts_dir)
    judge = make_judge_node(judge_llm, settings.prompts_dir)

    graph = StateGraph(PostState)
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer)
    graph.add_node("judge", judge)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "writer")
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
