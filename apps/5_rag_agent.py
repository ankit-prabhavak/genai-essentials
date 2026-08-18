from dotenv import load_dotenv
import os

load_dotenv()

from langchain_community.document_loaders import PyPDFLoader, PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
import streamlit as st


# data in st session
if "document_uploaded" not in st.session_state:
    st.session_state.document_uploaded = False

if "agent" not in st.session_state:
    st.session_state.agent = None

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "messages" not in st.session_state:
    st.session_state.messages = []


def process_document(path):

    # load the agent
    loader = PyPDFDirectoryLoader(path)
    docs = loader.load()

    # print(len(docs))
    # print(docs)

    # split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
    splitted_docs = splitter.split_documents(docs)


    # embedding and vector DB
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    vector_store = InMemoryVectorStore.from_documents(
        documents=splitted_docs,
        embedding=embeddings
    )


    # create an agent - tool, llm, prompt
    llm = ChatGroq(model="openai/gpt-oss-120b", streaming=True)


    @tool
    def retriever_tool(query: str):
        """
        Retrieve relevant information from the uploaded PDF documents.

        Use this tool to search the uploaded documents and return
        relevant content for answering the user's question.
        """

        # print(f"Tool Used for: {query}")

        docs = vector_store.similarity_search(
            query,
            k=10
        )

        if not docs:
            return "No relevant information was found in the uploaded documents."

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        return context
      


    system_prompt = """
    You are a helpful document question-answering assistant.

    You have access to a retriever_tool that searches the
    content of documents uploaded by the user.

    The uploaded documents are your primary source of information.

    IMPORTANT RULES:

    1. Always use retriever_tool when the user's question is
    related to information that may be present in the
    uploaded documents.

    2. Use the information retrieved from the documents as
    the primary source for your answer.

    3. Do not invent, assume, or fabricate information that
    is not supported by the uploaded documents.

    4. If the requested information cannot be found in the
    uploaded documents, clearly say:

    "I couldn't find that information in the uploaded documents."

    5. Do not assume what type of document the user has uploaded.
    It could be a resume, cover letter, marksheet, report,
    article, research paper, notes, book, or any other PDF.

    6. If the user asks multiple distinct questions, retrieve
    information for each question separately when necessary.

    7. If multiple retrieved documents contain relevant information,
    combine the information to provide a complete answer.

    8. Keep answers clear, concise, and easy to understand.

    9. If the user asks for a summary, summarize only the information
    available in the uploaded documents.

    10. If the user asks for specific facts, such as names, dates,
        numbers, qualifications, skills, organizations, technical
        details, or other document-specific information, verify them
        using the retriever_tool before answering.

    11. If the user's question is unrelated to the uploaded documents,
        you may answer using general knowledge, but clearly distinguish
        general knowledge from information found in the documents.

    12. Never claim that information comes from the uploaded documents
        unless that information was actually retrieved from them.
    """

    memory = InMemorySaver()

    agent = create_agent(
        model=llm,
        tools=[retriever_tool],
        system_prompt=system_prompt,
        checkpointer=memory
    )

    st.session_state.agent = agent
    st.session_state.document_uploaded = True



# upload UI
if not st.session_state.document_uploaded:
    uploaded = st.file_uploader(
       label="Select PDF files",
       type=["pdf"],
       accept_multiple_files=True
    )

    if uploaded:

        with st.spinner("Processing..."):
            path = "./doc_files/"

            for file in uploaded:
                with open(path + file.name, "wb") as f:
                    f.write(file.getvalue())

            process_document(path)
            st.rerun()

# chat UI

if st.session_state.document_uploaded and st.session_state.agent:

    for message in st.session_state.messages:
        role = message.get("role")
        content = message.get("content")

        st.chat_message(role).markdown(content)


    query = st.chat_input("Ask anything related to uploaded documents...")

    if query:

        st.session_state.messages.append({"role":"user", "content":query})
        st.chat_message("user").markdown(query)
        response = st.session_state.agent.invoke(
            {"messages": [{"role": "user", "content":query}]}, 
            {"configurable": {"thread_id": "rag1"}}
        )

        ans = response["messages"][-1].content       
        st.chat_message("assistant").markdown(ans)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": ans
            }
        )
       


