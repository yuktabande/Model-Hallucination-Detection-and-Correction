import re

def chunk_text(text, chunk_size=300, overlap=50):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) <= chunk_size:
            current += sentence + " "
        else:
            chunks.append(current.strip())
            current = sentence + " "

    if current:
        chunks.append(current.strip())

    # add overlap
    final = []
    for i in range(len(chunks)):
        start = max(0, i-1)
        final.append(" ".join(chunks[start:i+1]))
    return final