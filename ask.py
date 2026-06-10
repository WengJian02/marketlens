import chromadb
from anthropic import Anthropic

# load document and build chunk index
with open("nvda_risks.txt", "r", encoding="utf-8") as f:
    filing_text = f.read()

chunks = [
    line.strip().lstrip("- ").strip()
    for line in filing_text.split("\n")
    if line.strip().startswith("-")
]

chroma = chromadb.Client()
collection = chroma.create_collection("nvda_risks")
collection.add(
    documents=chunks,
    ids=[f"chunk-{i}" for i in range(len(chunks))],
)

client = Anthropic()

# MVP core system
def ask(question, n_results=4):
    # finds the chunks most relevant to the question
    results = collection.query(query_texts=[question], n_results=n_results)
    retrieved_chunks = results["documents"][0]

    # Builds a prompt with relevant chunks
    # Number them so Claude can cite which chunk it used, like [1], [2], etc.
    context = "\n".join(
        f"[{i+1}] {chunk}" for i, chunk in enumerate(retrieved_chunks)
    )
    prompt = f"""Answer the user's question using ONLY the context below, which
comes from NVIDIA's 10-K risk factors. Cite the chunk numbers you used, like [1].
Use the context to answer even if it doesn't use the exact words in the question — reason from what's
there. Only refuse if nothing in the context is relevant. Do not use outside knowledge.

CONTEXT:
{context}

QUESTION: {question}
"""
    # Generate the response using Claude
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.content[0].text

    # Show retrieved context (chunks)
    print(f"QUESTION: {question}\n")
    print("RETRIEVED CONTEXT:")
    print(context)
    print("\nANSWER:")
    print(answer)
    print("\n" + "=" * 60 + "\n")

ask("What are the risks related to China and export restrictions?")
ask("Could cyberattacks or data breaches hurt NVIDIA?")
ask("Does NVIDIA face any risks from its dividend policy?")
