# GenAI Essentials

A comprehensive, hands-on repository dedicated to mastering the core principles, architecture patterns, and production engineering of **Generative AI, Large Language Models (LLMs), LangChain, LangGraph, Retrieval-Augmented Generation (RAG), vector representations, and autonomous AI agents**.

This repository serves as an end-to-end technical reference containing structured lecture notes, Jupyter notebook implementations, production-style scripts, and full-stack prototyping demos.

---

## Detailed Curriculum and Concepts

### 1. LLM Fundamentals and API Architecture

* **Core Mechanisms:** Transformer foundations (Self-Attention, Multi-Head Attention), autoregressive decoding, and masked language modeling.
* **Tokenization and Limits:** Byte-Pair Encoding (BPE), WordPiece, token-to-word ratios, context window boundaries, and out-of-memory mitigation.
* **Sampling and Hyperparameters:** Temperature, Top-P (nucleus sampling), Top-K, presence penalty, frequency penalty, and repetition penalties.
* **Model Architectures:** Decoder-only (GPT family, Llama, Mistral), Encoder-only (BERT), and Encoder-Decoder (T5) trade-offs.
* **Inference and Serving:** API integration patterns, multi-provider routing via OpenRouter, and low-latency LPUs via Groq.

### 2. Prompt Engineering and Alignment

* **Message Hierarchy:** System instructions, developer roles, user inputs, and few-shot formatting.
* **Prompting Paradigms:** Zero-shot, few-shot with exemplars, Chain-of-Thought (CoT), Least-to-Most prompting, and Directional Stimulus prompting.
* **Reliability Engineering:** Preventing hallucination via grounding, defensive prompt framing against prompt injection, and output constraint enforcement.

### 3. LangChain and LCEL

* **LangChain Expression Language (LCEL):** Composition using the pipe operator (`|`), `Runnable` primitives, `RunnableParallel`, and `RunnablePassthrough`.
* **Model and Schema Wrappers:** Chat models, completion models, BaseMessage subclasses (`AIMessage`, `HumanMessage`, `SystemMessage`, `ToolMessage`).
* **Input and Output Parsing:** Structured outputs, Pydantic parsers, JsonOutputParser, and retry/fixing parsers.
* **Chains and Tools:** Composing sequential chains, integrating custom dynamic tools, and handling synchronous vs. asynchronous execution loops.

### 4. Agent Orchestration with LangGraph

* **Graph Architecture:** Defining deterministic and cyclic graphs with `StateGraph`, `START`, and `END` nodes.
* **State Management:** Schema design, state updates, custom reducers (e.g., message appending with `add_messages`), and schema validation.
* **Control Flow:** Conditional edges, routing functions, tool execution loops, and human-in-the-loop (HITL) approval breakpoints.
* **Persistence:** Checkpointers (MemorySaver, SQLite checkpointers), conversation thread isolation, and time-travel debugging.

### 5. Advanced Retrieval-Augmented Generation (RAG)

* **Ingestion Pipelines:** Multi-format document loading (PDF, Markdown, HTML, unstructured text).
* **Chunking Strategies:** Fixed-size chunking, recursive character splitting, semantic chunking, and markdown/document-aware chunking with token overlap.
* **Vector Stores and Search:** Cosine similarity, Euclidean distance (L2), Dot product, dense retrieval, and metadata filtering.
* **Advanced Query Routing:** Multi-query expansion, self-querying retrievers, contextual compression, reciprocal rank fusion (RRF), and hybrid search (BM25 + Dense).
* **Evaluation:** Assessing retrieval relevance, faithfulness, and answer relevance.

### 6. Embeddings and Vector Databases

* **Vector Semantics:** High-dimensional semantic space, dense representation vectors, and bi-encoder models.
* **Embedding Providers:** Hugging Face open-source models, OpenAI text-embedding models, and local inference via SentenceTransformers.
* **Vector Indexing:** Hierarchical Navigable Small World (HNSW), Inverted File Index (IVF), indexing performance vs. recall tradeoffs, and persistence strategies (Chroma, FAISS, Qdrant).

### 7. Autonomous AI Agents

* **Architectural Patterns:** ReAct (Reason + Act), Plan-and-Solve, and Reflexion architectures.
* **Tool Calling:** OpenAI-compatible function calling, schema definition via Pydantic, dynamic tool execution, and validation handling.
* **Agent Memory Systems:** Short-term conversational buffers, summary memory, vector-backed long-term episodic memory, and state persistence.

### 8. Structured Data and SQL Agents

* **Database Connectors:** SQLAlchemy engine wrappers, SQLite configurations, and read-only connection limits for safety.
* **SQL Toolkits:** Schema introspection, dialect detection, error handling, query validation, and self-correction on syntax errors.
* **Agent Capabilities:** Natural language to SQL synthesis, relational join queries, dynamic filtering, analytical aggregations, and safe transactional operations.

### 9. Interactive UIs with Streamlit

* **State and Session Handling:** Persistent multi-turn conversations using `st.session_state` and dynamic widget rerender management.
* **Streaming Responses:** Chunk-by-chunk token streaming using generators and LangChain's native callback handlers.
* **Chat Components:** Implementation with `st.chat_input`, `st.chat_message`, expandable status indicators (`st.status`), and custom sidebar configurations.

---

## Tech Stack and Dependencies

| Layer / Domain | Technology | Use Case |
| --- | --- | --- |
| **Language** | Python 3.10+ | Core development and script execution |
| **Frameworks** | LangChain, LangGraph | Core orchestration and cyclic graph-based agents |
| **Model Serving & APIs** | OpenRouter, Groq, OpenAI | LLM inference, API routing, and low-latency execution |
| **Data Validation** | Pydantic | Structured output parsing and tool schema definition |
| **Vector Search** | ChromaDB, FAISS | Vector indexing, persistence, and semantic similarity |
| **Embeddings** | Hugging Face, SentenceTransformers | Local and open-source dense vector generation |
| **Relational Data** | SQLite, SQLAlchemy | Relational data stores and Text-to-SQL workflows |
| **Front-End** | Streamlit | Chat user interfaces and interactive dashboards |
| **Tooling & Ops** | Git, GitHub, Python Dotenv | Version control, secrets management, and environment setup |

---

## Getting Started

### Prerequisites

* Python 3.10 or higher
* Virtual environment tool (`venv` or `conda`)
* API Keys (OpenAI, Groq, or OpenRouter)

### Setup Instructions

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/GenAI-Essentials.git
cd GenAI-Essentials

```

1. **Set up a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

```

1. **Install dependencies:**

```bash
pip install -r requirements.txt

```

1. **Configure environment variables:**
Create a `.env` file in the root directory:

```env
OPENAI_API_KEY="your-openai-api-key"
GROQ_API_KEY="your-groq-api-key"
OPENROUTER_API_KEY="your-openrouter-api-key"

```

1. **Run a Streamlit application:**

```bash
streamlit run apps/05_sql_database_agent.py

```
