import json
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def rewrite_query(original: str) -> list[str]:
    prompt = f"""Generate 3 alternative search queries for: "{original}"
Return ONLY a JSON array of 3 strings, nothing else.
Example: ["query one", "query two", "query three"]"""
    result = llm.invoke(prompt)
    try:
        return [original] + json.loads(result.content)
    except:
        return [original]
