# MarketLens Devlog
Last updated: 10/06/2026

### What is MarketLens?
An AI research assistant that answers natural-language questions about public companies using their SEC filings, with citations and honest refusal when the answer is not in the source.

This log tracks the engineering decisions, problems, and lessons behind the build.

Entries are newest first.

---

## Building a working RAG pipeline from scratch
**Entry Date:** 2026-06-09

### Goal
Set up the core of the system and prompt a natural language question about a public company's risk factors. AI will reply with answers only from the source provided and  cites from source. It will refuse to answer when source does not provide relevant details and not hallucinate unreliable/ fake answers.

### Implementations
A minimal Retrieval-Augmented Generation (RAG) pipeline over NVIDIA's 10-K risk factors:

- Copied NVDA 10-K risk factors and read .txt file
- Split text into chunks using chromadb
- Retrieved most relevant chunks based on question
- Build prompt based on using only relevant chunks
- Grounded generation with relevant chunks with instructions to answer from context
- Cites sources and refuses otherwise

### Decisions & Tradeoffs
- **Local Chroma over a hosted vector DB.** I wanted to understand retrieval mechanics without infrastructure overhead. Migrating to Postgres + pgvector is a deliberate later step, not a day-one need
- **Smallest/cheapest model for iteration.** During development the bottleneck is my iteration speed and cost, not model intelligence. I can upgrade the model once the pipeline is right

### Challenges Faced
#### 1. Section headers were polluting retrieval
My first chunker kept every line, so document headers *("Risks Related to
Demand, Supply, and Manufacturing")* became chunks and ranked above real content for some queries. Therefore, I kept only the lines that are actual risk statements.
#### 2. Precision-vs-refusal tradeoff
I tested with a question about China export risk. Retrieval correctly found
the relevant chunk: *"restrictions on the export of our products"*. Even though
the document never says "China." Meaning based search worked. But my prompt was strict *("only answer if the context contains the answer")*, so the model over-refused, it had the right information and still declined, because the exact word "China" wasn't present.

This introduced central tension in RAG. If the prompt is too strict, the model refuses even when it knows, which is unhelpful. On the other hand, if the prompt is too lose, it might make things up, making it unreliable.

### Evaluation
- A deliberate trick question *"risks from NVIDIA's dividend policy?"* where context was not in the filing was correctly refused. Instead of hallunicating an answer without proper citation, the model replied with *"I don't have information on that in the filing."*
- A direct question *"could cyberattacks hurt NVIDIA?"* was answered with a quote and a citation to the source chunk.

### What I learned
- Basic Minimum Viable Pipeline (MVP): Chunk → Embed → Retrieve → Generate
- Embeddings retrieve by *meaning*, which keyword search can't do.
- Grounding and honest refusal is the difference between a trustworthy tool and unreliability
- Retrieval quality is capped by chunk quality. Cleaning source data is required and important

### Next
Improve current implementation to read full length 10-K and deal with proper size based chunking, so that retrieval matters on real-world data.
