from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

# corpus
docs = [
    "Diffusion models are generative models based on iterative denoising.",
    "GANs consist of a generator and a discriminator trained adversarially.",
    "Transformers use self-attention to process sequences in parallel.",
    "Variational Autoencoders map data to latent space and reconstruct it.",
    "Flow-based models learn invertible transformations for density estimation."
]

# embedder
model = SentenceTransformer('BAAI/bge-small-en')

emb = model.encode(docs, normalize_embeddings=True)
dim = emb.shape[1]

# vector store
index = faiss.IndexFlatIP(dim)
index.add(emb)

# query
query = "What are diffusion models?"
query_emb = model.encode([query], normalize_embeddings=True)

# search
scores, idx = index.search(query_emb, 3)

# print results
for i, score in zip(idx[0], scores[0]):
    print(f"{score:.3f} -> {docs[i]}")