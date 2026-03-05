from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.4)

def extract_citations(web, rag) -> list[str]:
    citations = []; seen = set()
    for r in web:
        url = r.get("url","")
        if url and url not in seen:
            seen.add(url); citations.append(f"{r.get('title','Source')}: {url}")
    for r in rag:
        src = r.get("source","")
        if src and src not in seen:
            seen.add(src); citations.append(f"Internal doc: {src}")
    return citations

def writer_node(state: dict) -> dict:
    print("✍️  Writer agent running...")
    prompt = f"""Write a professional research report on: **{state["topic"]}**

Summary context: {state.get("summary","")}
Verified facts: {state.get("facts_verified",{}).get("verified_facts",[])}

Use this exact markdown structure:
# {state["topic"]} — Research Report
## Executive Summary
## Key Findings
## Detailed Analysis
## Conclusion
## Sources

Use inline citations [1], [2], etc."""
    result = llm.invoke(prompt)
    citations = extract_citations(state.get("web_results",[]), state.get("rag_results",[]))
    report = result.content
    if citations:
        report += "\n\n---\n### References\n" + "\n".join(f"[{i+1}] {c}" for i,c in enumerate(citations))
    return {**state, "final_report": report, "citations": citations}
