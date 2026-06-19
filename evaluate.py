import json
import chromadb
from anthropic import Anthropic

chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_collection("nvda_10k")
client = Anthropic()

# Adjustable number of chunks
N_RESULTS = 12

REFUSAL_PHRASE = "i don't have information"

def run_rag(question, n_results=N_RESULTS):
    results = collection.query(query_texts=[question], n_results=n_results)
    retrieved = results["documents"][0]
    context = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(retrieved))
    prompt = f"""Answer the question using ONLY the context below, from NVIDIA's
10-K. Reason from what the context says even if it doesn't use the exact words.
Cite chunk numbers like [2]. If nothing in the context is relevant, say exactly
"I don't have information on that in the filing."

CONTEXT:
{context}

QUESTION: {question}
"""
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text, retrieved

# LLM-as-judge to grade the actual answer against the expected one
def judge_answer(question, expected, actual):
    prompt = f"""You are grading a financial Q&A system. Compare the SYSTEM ANSWER
to the EXPECTED ANSWER for the QUESTION. Reply with ONE word only:
- CORRECT if the system answer captures the key facts of the expected answer
- PARTIAL if it is partly right or missing important pieces
- WRONG if it is incorrect or contradicts the expected answer

QUESTION: {question}
EXPECTED ANSWER: {expected}
SYSTEM ANSWER: {actual}

Your one-word grade:"""
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip().upper()

with open("golden_set.json", "r", encoding="utf-8") as f:
    golden = json.load(f)

retrieval_hits = 0
retrieval_total = 0
answer_correct = 0
refusal_correct = 0
refusal_total = 0

print(f"Running {len(golden)} questions at N_RESULTS={N_RESULTS}\n" + "=" * 70)

for item in golden:
    q = item["question"]
    answer, retrieved = run_rag(q)
    # sets T/F for refusal questions based on whether the answer contains the refusal phrase
    refused = REFUSAL_PHRASE in answer.lower()

    print(f"\n[{item['id']}] ({item['type']}) {q}")
    
    # item["must_retrieve_keyword"] exist in everything except the "should_refuse" questions, so we can use it to determine if we should check retrieval
    if item["must_retrieve_keyword"]:
        retrieval_total += 1
        joined = " ".join(retrieved).lower()
        # checks to see if the keyword is in the retrieved chunks, and counts it as a hit if so
        hit = item["must_retrieve_keyword"].lower() in joined
        retrieval_hits += hit # True == 1 / False == 0
        print(f"    retrieval: {'HIT ' if hit else 'MISS'} (looking for '{item['must_retrieve_keyword']}')")
        
    # item["should_refuse"] is True for questions that should be refused, and False for questions that should be answered.
    if item["should_refuse"]:
        refusal_total += 1
        ok = refused
        refusal_correct += ok
        print(f"    refusal:   {'CORRECT (refused)' if ok else 'FAILED (did not refuse!)'}")
    else:
        # difference between must retrieve and should_refuse is that must_retrieve is about whether the retrieved chunks contain a keyword, while should_refuse is about whether the final answer contains a refusal phrase. So we only judge the answer if it's not a refusal case.
        grade = judge_answer(q, item["expected_answer"], answer)
        answer_correct += (grade == "CORRECT")
        print(f"    answer:    {grade}")

print("\n" + "=" * 70)
print("SCORECARD")
print(f"  Retrieval:  {retrieval_hits}/{retrieval_total} chunks found the right keyword")
print(f"  Answers:    {answer_correct}/{retrieval_total} graded CORRECT")
print(f"  Refusals:   {refusal_correct}/{refusal_total} handled honestly")
