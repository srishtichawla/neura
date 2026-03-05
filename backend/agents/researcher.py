import os
from tavily import TavilyClient
from dotenv import load_dotenv
load_dotenv()

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def researcher_node(state: dict) -> dict:
    print("🔍 Researcher agent running...")
    results = []
    for query in state.get("queries", [state["topic"]])[:4]:
        try:
            resp = tavily.search(query=query, max_results=4, include_raw_content=False)
            for r in resp.get("results", []):
                results.append({"title": r.get("title",""), "content": r.get("content",""),
                                 "url": r.get("url",""), "score": r.get("score",0)})
        except Exception as e:
            print(f"  ⚠️  Tavily error: {e}")
    return {**state, "web_results": results}
