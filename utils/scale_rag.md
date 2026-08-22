# **Executive Summary**

Standard AI search (RAG) slows down and gets expensive when reading large documents. Searching a 10,000-page file line-by-line takes too long.

This proposal transforms standard AI search into a **High-Performance Computing (HPC)** system by separating the process into two independent parts:

1. **Ingestion (Preparation):** Read, organize, and store the document *once* ahead of time.
2. **Retrieval (Answering):** Search millions of entries and answer questions in *milliseconds*.

---

## **1. The Core Concept**

**💡 The Analogy:**

* **Slow Approach:** Every time a doctor asks a question, an assistant reads a 10,000-page medical book from start to finish.
* **HPC Approach:** Before the clinic opens, an archivist reads the book once, cuts it into small flashcards, organizes them into a catalog by topic, and notes page numbers. When the doctor asks a question, the assistant checks the catalog, pulls the exact 3 flashcards needed, and reads only those.

```text
OFFLINE INGESTION PIPELINE (Done Once Ahead of Time)
[10,000-Page File] ➔ [Distributed Reading] ➔ [Smart Cutting] ➔ [GPU Vectorizing] ➔ [Bulk DB Save]

ONLINE RETRIEVAL PIPELINE (Done in Milliseconds on User Query)
[User Question] ➔ [Convert Question] ➔ [Fast Index Lookup] ➔ [Pick Top 3 Cards] ➔ [LLM Answer]

```

---

### **2. Phase 1: High-Performance Ingestion Pipeline**

Instead of using one standard computer processor to read a huge file sequentially, processing is split across a network of machines.

**Step-by-Step Breakdown:**

* **Distributed Computing (Ray/Spark):** Divides the 10,000-page document into smaller pieces and sends them to multiple server nodes to read simultaneously.
* **Structure-Aware Parsing:** Extracts text along with headings, tables, and page numbers to preserve structural context.
* **Smart Chunking:** Cuts the document into small, uniform snippets (~300 words each).
* **GPU Batch Embeddings:** Converts thousands of text snippets into numerical coordinates (vectors) at once using dedicated GPU servers.
* **Bulk Database Load:** Streams the snippets directly into the database using PostgreSQL's high-speed `COPY` command rather than saving line-by-line.

---

### **3. Phase 2: High-Performance Database Storage (pgvector)**

To instantly search millions of text vectors, the database uses an **HNSW Index** (Hierarchical Navigable Small World).

**💡 The Analogy:**
Think of the HNSW index as a multi-tiered highway system:

* **Layer 1 (Highway):** Directs traffic to broad topics (e.g., separating Sports from Medicine).
* **Layer 2 (State Roads):** Narrow the search (e.g., Cardiology within Medicine).
* **Layer 3 (City Streets):** Leads straight to the specific address (the exact snippet from Page 10,000).

**Key Storage Optimizations:**

* **RAM Caching:** Keeps the entire search index inside the server's high-speed RAM memory so it never has to read from a slow disk drive.
* **Table Partitioning:** Breaks giant database tables into smaller sub-tables (e.g., by department or year). The search engine skips entire irrelevant sub-tables instantly.

---

### **4. Phase 3: Low-Latency Retrieval Engine**

When a user asks a question, the system finds the answer without making the user wait.

**Step-by-Step Breakdown:**

* **Vector Conversion:** Converts the user's question into numerical coordinates.
* **Metadata Filtering:** Uses standard SQL rules to instantly skip out-of-scope files (e.g., matching department or date).
* **Two-Stage Search:**
* *Stage 1 (Broad Net):* Uses `pgvector` to pick the top 50 likely snippet candidates in under 10 milliseconds.
* *Stage 2 (Refinement):* Uses a specialized Reranker model to score those 50 snippets and pick the absolute 3 best matches.
* **Async Execution (LangChain LCEL):** Handles hundreds of incoming queries simultaneously without blocking the system.
* **Final Answer Generation:** Sends only the 3 relevant text snippets (~1,000 words total) to the AI model, allowing it to generate an accurate response in seconds.

---

### **5. Technology Stack Summary**

| System Layer | Prototype Setup | Enterprise HPC Setup |
| --- | --- | --- |
| **Data Processing** | Single Python Scripts | Distributed Cluster (Ray / Apache Spark) |
| **Vector Creation** | Cloud APIs (Slow) | Private GPU Clusters (vLLM / TGI) |
| **Vector Storage** | Local Files (Chroma / FAISS) | PostgreSQL (`pgvector` with HNSW Index) |
| **Scalability** | Single Giant Table | Table Partitioning + Connection Pooling |
| **Application Layer** | Standard Sequential Code | Asynchronous Framework (LangChain LCEL) |
