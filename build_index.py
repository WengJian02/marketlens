import chromadb

with open("nvda_10k.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Splitting text into overlapping chunks of ~300 words
def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + chunk_size])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

chunks = chunk_text(text)
print(f"Split 10-K into {len(chunks)} chunks.")
print(f"\nExample chunk (#50)\n{chunks[50]}")

# Setting up persistent chromadb index
chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_or_create_collection("nvda_10k")

# Checking if the collection is empty before adding chunks
if collection.count() == 0:
    collection.add(
        documents=chunks,
        ids=[f"chunk-{i}" for i in range(len(chunks))],
    )
    print(f"Index saved")
else:
    print(f"Index already exists")
