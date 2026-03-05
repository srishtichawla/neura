from langgraph.graph import StateGraph, END
from typing import TypedDict
from agents.researcher import researcher_node
from agents.rag_agent import rag_retriever_node
from agents.fact_checker import fact_checker_node
from agents.summarizer import summarizer_node
from agents.writer import writer_node

class ResearchState(TypedDict, total=False):
    topic: str
    queries: list
    web_results: list
    rag_results: list
    facts_verified: dict
    summary: str
    final_report: str
    citations: list

def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("rag_retriever", rag_retriever_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("fact_checker", fact_checker_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("writer", writer_node)
    graph.set_entry_point("rag_retriever")
    graph.add_edge("rag_retriever", "researcher")
    graph.add_edge("researcher", "fact_checker")
    graph.add_edge("fact_checker", "summarizer")
    graph.add_edge("summarizer", "writer")
    graph.add_edge("writer", END)
    return graph.compile()
