from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

def summarizer_node(state: dict) -> dict:
    print("📝 Summarizer agent running...")
    facts = state.get("facts_verified", {}).get("verified_facts", [])
    prompt = f"""Write a 3-paragraph analytical summary about: {state["topic"]}
Key facts:
{chr(10).join(f"- {f}" for f in facts[:20])}
Cover: overview, key findings, significance."""
    result = llm.invoke(prompt)
    return {**state, "summary": result.content}
