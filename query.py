import chromadb
from anthropic import Anthropic

# Connect to persistent local chromadb
chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_collection("nvda_10k")

client = Anthropic()

def ask(question, n_results=10):
    results = collection.query(query_texts=[question], n_results=n_results)
    retrieved = results["documents"][0]
    context = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(retrieved))
    prompt = f"""Answer the question using ONLY the context below, taken from
NVIDIA's most recent 10-K. Reason from what the context says even if it doesn't
use the exact words in the question. Cite the chunk numbers you used, like [2].
If nothing in the context is relevant, say "I don't have information on that in
the filing."

CONTEXT:
{context}

QUESTION: {question}
"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"QUESTION: {question}\n")
    print("ANSWER:")
    print(response.content[0].text)
    print("\n" + "=" * 70 + "\n")


ask("What did NVIDIA say about China and export restrictions on its products?")
ask("What impacted NVIDIA's gross margins recently?")
ask("How does NVIDIA describe its competition?")
