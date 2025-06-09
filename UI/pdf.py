import streamlit as st
import os
from PyPDF2 import PdfReader
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import init_chat_model

from dotenv import load_dotenv

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        try:
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            st.error(f"Error reading {pdf.name}: {e}")

    return text.strip()

def get_text_chunks(raw_text):
    text_spliter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    text_chunks = text_spliter.split_text(raw_text)
    return text_chunks

def get_vector_store(text_chunks):

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = FAISS.from_texts(text_chunks, embeddings)

    return vector_store

def get_conversation_chain(vector_store):

    llm = init_chat_model("google_genai:gemini-2.0-flash")

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory
    )

    return conversation_chain

def handle_user_question(user_question):
    response = st.session_state.conversation({'question': user_question})

    st.session_state.chat_history = response["chat_history"]

    for i,msg in reversed(list(enumerate(st.session_state.chat_history))):
        if i%2==0:
            st.chat_message("user").markdown(msg.content)
        else:
            st.chat_message("assistant").markdown(msg.content)

def main():
    load_dotenv()
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.set_page_config(page_title="Chat with PDF", page_icon=":books:")

    st.header("Chat with PDF")
    user_question = st.text_input("Ask me anything about the PDF content:")

    if user_question:
        with st.spinner("Retrieving....."):
            handle_user_question(user_question)



    with st.sidebar:
        st.subheader("Your Documents")
        pdf_docs = st.file_uploader("Upload PDF", accept_multiple_files=True, type=["pdf"])
        if st.button("Upload"):
            with st.spinner("Processing..."):


                try:
                    #Get PDF Text
                    raw_text = get_pdf_text(pdf_docs)

                    #get text chunks
                    text_chunks = get_text_chunks(raw_text)

                    #get vector store
                    vector_store = get_vector_store(text_chunks)
                    st.success("PDF processed successfully!")
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")
                    return

                st.session_state.conversation = get_conversation_chain(vector_store)




if __name__ == "__main__":
    main()
