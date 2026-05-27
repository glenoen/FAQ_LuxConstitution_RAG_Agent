# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/besser-agentic-framework") # Replace with your directory path

import json
import logging
import operator
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from baf.core.agent import Agent
from baf.library.transition.events.base_events import *
from baf.nlp.llm.llm_huggingface import LLMHuggingFace
from baf.nlp.llm.llm_huggingface_api import LLMHuggingFaceAPI
from baf.nlp.llm.llm_openai_api import LLMOpenAI
from baf.nlp.llm.llm_replicate_api import LLMReplicate
from baf.core.session import Session
from baf.nlp.intent_classifier.intent_classifier_configuration import (
    LLMIntentClassifierConfiguration,
    SimpleIntentClassifierConfiguration,
)
from baf.nlp.speech2text.openai_speech2text import OpenAISpeech2Text
from baf.nlp.text2speech.openai_text2speech import OpenAIText2Speech
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from baf import nlp
from baf.nlp.rag.rag import RAG
from lxml import etree

AKOMA_NS = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD13"}
# Configure the logging module
logging.basicConfig(
    level=logging.INFO, format="{levelname} - {asctime}: {message}", style="{"
)


# Create the bot
agent = Agent("FAQ_LuxConstitution_RAG_Agent")
# Load bot properties stored in a dedicated file
agent.load_properties("config.yaml")

# Define the platform your chatbot will use


platform = agent.use_websocket_platform(use_ui=True)

##############################
# RAG CONFIGURATIONS
##############################

articlesofluxembourgishconstitution_vector_store = Chroma(
    embedding_function=OpenAIEmbeddings(
        openai_api_key=agent.get_property(nlp.OPENAI_API_KEY)
    ),
    persist_directory="vector_store/articlesofluxembourgishconstitution",
)

articlesofluxembourgishconstitution_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=100
)

articlesofluxembourgishconstitution_rag = RAG(
    agent=agent,
    vector_store=articlesofluxembourgishconstitution_vector_store,
    splitter=articlesofluxembourgishconstitution_splitter,
    llm_name="gpt-5-mini",
    k=4,
    num_previous_messages=0,
)


# LLMs
gpt_5_mini = LLMOpenAI(
    agent=agent,
    name="gpt-5-mini",
    parameters={},
    num_previous_messages=1,
)

default_llm = gpt_5_mini

##############################
# INTENTS
##############################


##############################
# CUSTOM CONDITIONS
##############################


##############################
# STATES
##############################


Greeting = agent.new_state("Greeting", initial=True)
Idle = agent.new_state("Idle")
Response = agent.new_state("Response")
LatestModifications = agent.new_state("LatestModifications")
LoadingDocument = agent.new_state("LoadingDocument")


# Greeting
def Greeting_body(session: Session):
    reply_text = "Hi, I am your assistant, I can answer questions related to the Luxembourgish Constitution."
    session.reply(reply_text)


Greeting.set_body(Greeting_body)
Greeting.go_to(LatestModifications)


# Idle
def Idle_body(session: Session):
    reply_text = "What would you like to know about the Constitution?"
    session.reply(reply_text)


Idle.set_body(Idle_body)
Idle.when_event(ReceiveTextEvent()).go_to(Response)


# Response
def Response_body(session: Session):
    rag_message = session.run_rag(session.event.message)
    platform.reply_rag(session, rag_message)


Response.set_body(Response_body)
Response.go_to(Idle)


# LatestModifications
def LatestModifications_body(session: Session):
    reply_text = "(SPARQL) Latest information about modifications of the Luxembourgish Constitution"
    session.reply(reply_text)
    endpoint = "https://data.legilux.public.lu/sparqlendpoint"
    query_file = "query.rq"

    df = sparql_query_to_df(endpoint, query_file)
    platform.reply_dataframe(session, df)


def sparql_query_to_df(endpoint_url, query_file):
    """
    Executes a SPARQL query loaded from a file and returns the results in a pandas DataFrame.

    Args:
        endpoint_url (str): The URL of the SPARQL endpoint.
        query_file (str): The file path containing the SPARQL query.

    Returns:
        pd.DataFrame: A dataframe containing the results.
    """
    # Load query from file
    with open(query_file, "r", encoding="utf-8") as f:
        query = f.read()

    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # Parse results to DataFrame
    columns = results["head"]["vars"]
    out = []
    for result in results["results"]["bindings"]:
        row = []
        for col in columns:
            value = result.get(col, {}).get("value", None)
            row.append(value)
        out.append(row)
    return pd.DataFrame(out, columns=columns)


LatestModifications.set_body(LatestModifications_body)
LatestModifications.go_to(LoadingDocument)


def LoadingDocument_body(session: Session):
    reply_text = "I am loading the Constitution document now so you can ask me questions about it."
    embed_akomantoso_articles('articlesofluxembourgishconstitution/eli-etat-leg-constitution-1868-10-17-n1-consolide-20230701-fr-xml.xml',articlesofluxembourgishconstitution_rag)
    session.reply(reply_text)


def load_akoma_ntoso_articles(xml_path):
    """
    Parses Akoma Ntoso XML and returns a list of (article_id, article_text) using explicit akn namespace.
    """
    articles = []
    with open(xml_path, "rb") as f:
        tree = etree.parse(f)
    for article in tree.xpath(
        "/akn:akomaNtoso/akn:act/akn:body//akn:article", namespaces=AKOMA_NS
    ):
        # Gather all <alinea> texts within this <article>
        alineas = [
            alinea.lstrip()
            for alinea in article.xpath(".//akn:alinea//text()", namespaces=AKOMA_NS)
            if alinea
        ]
        fulltext = "".join(alineas)
        # Prefer 'eId', fallback to 'id', else auto id
        article_id = (
            article.get("eId") or article.get("id") or f"auto_{len(articles)+1}"
        )
        articles.append({"id": article_id, "text": fulltext})
    return articles


def embed_akomantoso_articles(xml_file_path, rag: RAG):
    """
    Loads Akoma Ntoso XML, processes each article's fulltext (from alineas),
    splits, and adds to the vector store.
    """
    articles = load_akoma_ntoso_articles(xml_file_path)
    documents = []
    for art in articles:
        doc = Document(
            page_content=art["text"], metadata={"source": art["id"], "page": art["id"]}
        )
        documents.append(doc)
    # chunked_documents = rag.splitter.split_documents(documents)
    rag.vector_store.add_documents(documents)
    # Now print what was added
    vector_data = rag.vector_store.get()
    docs = vector_data["documents"]
    metas = vector_data["metadatas"]

    for i, (doc, meta) in enumerate(zip(docs, metas), 1):
        print(f"--- Document {i} ---")
        print(doc)
        print("Metadata:", meta)
        print()
        print(f"Embedded {len(documents)} article chunks from {xml_file_path}")


LoadingDocument.set_body(LoadingDocument_body)
LoadingDocument.go_to(Idle)


# RUN APPLICATION

if __name__ == "__main__":
    agent.run()
