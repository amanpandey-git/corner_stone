# VIVA - likely examiner questions

Each step adds 3-5 questions with short answers when it finishes.

## Step 0 - Setup & architecture
- **Q: Why write ARCHITECTURE.md before code?** A: Contracts (inputs, outputs, errors) are agreed first, so modules can be built and tested independently and Stage 2 can plug in without rewrites.
- **Q: Why HNSW instead of a flat index?** A: A flat index compares the query with every vector (O(N)). HNSW walks a layered proximity graph and visits only a small fraction (roughly O(log N)), trading a little recall for large speed-ups as the corpus grows.
- **Q: hnswlib vs faiss?** A: Same algorithm. hnswlib has no Windows wheel and needs a C++ compiler, so I used faiss `IndexHNSWFlat` behind my own interface; the rest of the code does not know which backend is used.
- **Q: Why a manifest file next to the index?** A: Vectors from different models are not comparable. The manifest records model, dimension, space and normalisation, and loading refuses a mismatch instead of silently returning garbage.

## Step 1 - Extraction
- **Q: How do you detect a scanned page?** A: Almost no extractable text (< 25 chars) while the page contains an image. It is flagged `needs_ocr` with a reason and counted; text is kept for Stage 2 OCR. A page with no text and no image is flagged `empty`.
- **Q: How are headings found in a PDF?** A: PDFs have no heading tags, so I compare font sizes: body size is the size carrying most characters in the document; lines at >= 1.15x that are short are headings, ranked into levels by size.
- **Q: Why PyMuPDF?** A: Fast, pure wheels on Windows, gives per-span font size and image blocks, which I need for headings and scan detection.
- **Q: Why remove headers/footers, and how?** A: A repeated footer ("Dr X, MITS-DU") would be embedded into every chunk and pollute similarity. I count lines (digits/punctuation ignored) at the top/bottom of each page and remove those appearing on at least half the pages.
- **Q: Why NFC and not NFKC normalisation?** A: NFKC rewrites symbols (e.g. superscripts, some maths characters); NFC keeps them. Ligatures are expanded explicitly instead.
- **Q: Why does DOCX have no page numbers?** A: Page breaks in DOCX depend on rendering (fonts, printer), so a page number would be invented. I store heading sections with paragraph ranges, which are stable.

## Step 2 - Chunking
- **Q: Why chunk at all, and why 256 tokens with 48 overlap?** A: The embedding model reads up to 512 tokens and one vector per chunk must represent one idea; 256 is about 1-2 paragraphs, so a hit points to a precise page. Overlap (~19%) makes sure a sentence cut by a boundary is complete in at least one chunk.
- **Q: What is structure-aware chunking?** A: I split at headings first (so a chunk never mixes two topics), and only then by token windows inside long sections. A heading line stays at the top of its chunk so the topic words are embedded with the content.
- **Q: What if a section or sentence is longer than the model limit?** A: It is split (by sentence, then by words), never truncated; hard_max is 480 < 512. A test with a 400-word unpunctuated sentence proves nothing is lost.
- **Q: What happens to tiny fragments like a lone heading?** A: Under 40 tokens they are merged into the next chunk, otherwise they would be retrieved as meaningless hits.
- **Q: Why count tokens with the model tokenizer, not words?** A: The limit that matters is in model tokens (WordPiece splits rare words into pieces); words under-count.
## Step 3 - Embeddings
- **Q: What is the bge query prefix and why only on queries?** A: bge-small-en-v1.5 was trained with the instruction "Represent this sentence for searching relevant passages: " in front of short search queries, so a question lands close to the passages that answer it. Passages are documents, not questions, so they get no prefix. The prefix is part of the model contract, so it lives in config.yaml and is tested.
- **Q: Why normalise vectors to unit length?** A: With unit vectors, cosine similarity equals the plain inner product, which is what the index computes fastest; it also removes length effects so only direction (meaning) matters, and scores fall in a fixed -1..1 range that can be compared across queries.
- **Q: Why bge-small-en-v1.5 and not a bigger model?** A: 33M parameters (about 130 MB), 384 dimensions, strong English retrieval for its size, and it runs on 4 CPU cores in 8 GB RAM. Bigger models would be slower with little gain on a few hundred chunks.
- **Q: How do you embed 300+ pages without running out of memory?** A: Chunks are encoded in batches of 32; only the small (n x 384 float32) result matrix is kept, so memory is bounded by the batch, not the document.
- **Q: How do you know the embeddings are sensible?** A: Tests check dimension 384, unit norm, that a deadlock question scores higher against a deadlock passage than a bread recipe, and that batched and single encoding agree.
## Step 4 - Index + store
- **Q: What do M, ef_construction and ef_search control?** A: M is how many links each node keeps in the graph (more links = better recall, more memory). ef_construction is how wide the search is while building (better graph, slower build). ef_search is how many candidates are explored per query (higher = better recall, slower query); it must be at least k, so I use max(ef_search, k).
- **Q: Why IndexIDMap2 and add_with_ids?** A: HNSW numbers vectors 0,1,2... by insertion. The wrapper lets me give each vector its chunk_id as label, so a search result is directly a SQLite primary key; no separate lookup table to keep in sync.
- **Q: How do you delete a document if HNSW cannot remove vectors?** A: Soft delete: SQLite marks the chunks deleted and search filters them out (over-fetching so k live results remain). Labels are never reused (AUTOINCREMENT), so a stale vector can never be confused with a new chunk.
- **Q: What does the manifest protect against?** A: Opening an index built with another model, dimension or metric. Vectors from different models live in different spaces, so results would be silently meaningless. The manifest records model name+revision, dimension, space and normalisation, and load raises ModelMismatch if any differs or the manifest is missing.
- **Q: Why a unit-norm check in add()?** A: The index uses inner product as cosine. A non-normalised vector would silently rank by length instead of meaning, so it is rejected.
## Step 5 - Search + CLI
## Step 6 - Verification
## Step 7 - Demo UI
## Step 8 - Wrap-up
