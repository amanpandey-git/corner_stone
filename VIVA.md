# VIVA - likely examiner questions

Each step adds 3-5 questions with short answers when it finishes.

## Step 0 - Setup & architecture
- **Q: Why write ARCHITECTURE.md before code?** A: Contracts (inputs, outputs, errors) are agreed first, so modules can be built and tested independently and Stage 2 can plug in without rewrites.
- **Q: Why HNSW instead of a flat index?** A: A flat index compares the query with every vector (O(N)). HNSW walks a layered proximity graph and visits only a small fraction (roughly O(log N)), trading a little recall for large speed-ups as the corpus grows.
- **Q: hnswlib vs faiss?** A: Same algorithm. hnswlib has no Windows wheel and needs a C++ compiler, so I used faiss `IndexHNSWFlat` behind my own interface; the rest of the code does not know which backend is used.
- **Q: Why a manifest file next to the index?** A: Vectors from different models are not comparable. The manifest records model, dimension, space and normalisation, and loading refuses a mismatch instead of silently returning garbage.

## Step 1 - Extraction
## Step 2 - Chunking
## Step 3 - Embeddings
## Step 4 - Index + store
## Step 5 - Search + CLI
## Step 6 - Verification
## Step 7 - Demo UI
## Step 8 - Wrap-up
