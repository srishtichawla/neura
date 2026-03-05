import json
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def fact_checker_node(state: dict) -> dict:
    print("✅ Fact-checker agent running...")
    sources = [{"content": r["content"], "source": r.get("url") or r.get("source","")}
               for r in (state.get("web_results",[])[:8] + state.get("rag_results",[])[:4])]
    prompt = f"""Topic: {state["topic"]}
Extract verified key facts from these sources. Remove duplicates.
Sources: {json.dumps(sources)[:6000]}
Return ONLY valid JSON (no markdown):
{{"verified_facts": ["fact 1", ...], "key_sources": ["url1", ...], "contradictions": []}}"""
    result = llm.invoke(prompt)
    content = result.content.strip().lstrip("```json").lstrip("```").rstrip("```")
    try:
        parsed = json.loads(content)
    except:
        parsed = {"verified_facts": [], "key_sources": [], "contradictions": []}
    return {**state, "facts_verified": parsed}
