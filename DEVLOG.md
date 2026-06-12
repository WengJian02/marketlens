# MarketLens Devlog
Last updated: 12/06/2026

### What is MarketLens?
An AI research assistant that answers natural-language questions about public companies using their SEC filings, with citations and honest refusal when the answer is not in the source.

This log tracks the engineering decisions, problems, and lessons behind the build.

Entries are newest first.

---
## Reading full 10-k with size based chunking
**Entry Date:** 11/06/2026

### Goals
- Get metadata and text for the full-length 10-K, and chunk it based on size limits instead of arbitrary line breaks
- Persist chunks and metadata in a local chromadb instance, so that tokens are more efficiently used for retrieval and generation
- Query from persistent chromadb to ask more in-depth questions

### Implementations
A full 10-K read, chunk based on size limits and query from persistent chromadb:
- Requests to SEC EDGAR API to get metadata and text for full-length 10-K
- Stored chromadb index locally
- Query from chromadb with more in-depth questions about 10-K with increased chunk size to capture more context

### Decisions & Tradeoffs
- **Size-based chunking over line-based.** Line breaks in the raw text file were arbitrary and often split important context. Size-based chunking ensures that each chunk has enough content to be meaningful for retrieval, even if it means some overlap and redundancy
- **Local chromadb for persistencee.** Allows for faster retrieval and iteration during development without the overhead of setting up a hosted vector database. It also makes it easier to inspect the indexed data and debug retrieval issues
- **Increased chunk size.** Larger chunks capture more context, which can improve retrieval relevance, but also means fewer total chunks and potentially less granularity.
- **Balancing retrieval precision and generation quality.** Larger chunks can improve retrieval relevance, but may also include more irrelevant information, which can make it harder for the model to generate focused answers

### Challenges Faced
- **Parsing and cleaning the full 10-K text.** The raw text from the SEC EDGAR API includes a lot of boilerplate, formatting artifacts, and non-content sections. Cleaning this data to extract meaningful chunks was a significant challenge, requiring careful handling of section headers, footnotes, and other non-content elements
- **Chunking strategy.** Finding the right balance between chunk size and overlap was tricky. Too small chunks led to loss of context, while too large chunks made retrieval less precise and increased token usage during generation
- **Retrieval relevance.** Ensuring that the retrieved chunks were relevant to the query was a challenge, especially with larger chunks that contained more information. This required iterative tuning of the chunking strategy and retrieval parameters
- **Model performance.** With larger chunks, the model had to sift through more information to generate answers, which sometimes led to less focused responses. This required careful prompt engineering to guide the model to extract relevant information from the retrieved chunks

### Evaluation
- Successfully retrieved relevant chunks for in-depth questions about the 10-K, such as specific risk factors and financial metrics, demonstrating improved retrieval relevance with size-based chunking.
- The model was able to generate more accurate and contextually grounded answers based on the retrieved chunks, although there were still instances where the model struggled to focus on the most relevant information within larger chunks, indicating room for improvement in prompt engineering and chunking strategy
- The local chromadb instance allowed for efficient retrieval and iteration during development, and made it easier to inspect the indexed data and debug retrieval issues

### What I learned
- Size-based chunking is more effective than line-based chunking for capturing meaningful context in documents like 10-K filings, but it requires careful tuning of chunk size and overlap to balance retrieval relevance and token usage
- Cleaning and parsing raw text data from sources like the SEC EDGAR API is a critical step in building a RAG pipeline, as it directly impacts the quality of the indexed data and the relevance of retrieved chunks
- Prompt engineering becomes even more important with larger chunks, as the model needs clear guidance to extract relevant information from a larger pool of content during generation
- Local persistence with chromadb can speed up development and make it easier to debug retrieval issues, but it may not be suitable for production use, where a hosted vector database might be necessary for scalability and reliability

### Next
Build an evaluation harness and golden set of questions and answers to systematically test retrieval and generation quality.

---

## Building a minimal RAG pipeline from scratch
**Entry Date:** 09/06/2026

### Goals
- Set up the core of the system and prompt a natural language question about NVDA risk factors.
- Model will reply with answers only from the source provided and cites from it
- Refuse to answer when source does not provide relevant details and not hallucinate unreliable/ fake answers

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
