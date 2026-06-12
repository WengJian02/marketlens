import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "KWOK WENG JIAN KWOKWENGJIAN02@gmail.com"}
CIK = "0001045810"

url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
data = requests.get(url, headers=HEADERS).json()

recent = data["filings"]["recent"]
forms = recent["form"]
accessions = recent["accessionNumber"]
primary_docs = recent["primaryDocument"]
dates = recent["filingDate"]

i = forms.index("10-K")
accession = accessions[i].replace("-", "")
primary_doc = primary_docs[i]
print(f"Found 10-K filed {dates[i]} (accession {accessions[i]})")


doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{accession}/{primary_doc}"
print(f"Downloading: {doc_url}")
html = requests.get(doc_url, headers=HEADERS).text
print(f"Raw HTML size: {len(html):,} characters")

with open("nvda_10k.htm", "w", encoding="utf-8") as f:
    f.write(html)

soup = BeautifulSoup(html, "html.parser")
text = soup.get_text(separator="\n")
lines = [line.strip() for line in text.split("\n")]
clean = "\n".join(line for line in lines if line)

with open("nvda_10k.txt", "w", encoding="utf-8") as f:
    f.write(clean)

print(f"\nSaved nvda_10k.txt: {len(clean):,} characters (~{len(clean)//4:,} tokens)")
