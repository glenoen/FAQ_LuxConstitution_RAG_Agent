# FAQ_LuxConstitution_RAG_Agent

## Overview

This repository hosts an application developed with **besser** that provides answers to questions regarding the Luxembourgish Constitution. The application leverages the latest official consolidated versions of the Constitution, allowing users to access up-to-date information and direct links to official documents on the [Legilux portal](https://legilux.public.lu).

## How It Works

- **Startup and Version Info:**  
  Upon launch, the application fetches information about the latest consolidation versions of the Luxembourg Constitution with a SPARQL query to the endpoint [https://data.legilux.public.lu/sparqlendpoint](https://data.legilux.public.lu/sparqlendpoint). Users are shown these details, including links to view the documents directly on [Legilux](https://legilux.public.lu).


- **Vector Database Creation:**  
  The application utilizes a local copy of the latest version of the Constitution document to create a vector database, with individual articles represented as vectors for efficient retrieval and embedding.

- **Akomantoso XML Format:**  
  The constitutional document is provided in the [Akomantoso](https://www.oasis-open.org/standard/akn-v1-0/) XML format, obtained from the official Legilux portal.  
  *Akomantoso* is an open standard XML schema designed specifically for legislative, legal, and parliamentary documents. It allows for fine-grained structuring—enabling the extraction of articles on an individual basis. This level of granularity would not be possible with a traditional PDF, which lacks explicit structure for article-level segmentation.

## Features

- Search and answer questions about the Luxembourg Constitution.
- Always up-to-date consolidation links.
- Enhanced article-level query and retrieval thanks to structured legal XML.


## Answer Basis and Example Questions

When queried, the system returns the specific articles of the Luxembourg Constitution that formed the basis of its response. This ensures transparency and allows users to consult the original legal sources for further clarification.

Below are some example questions you can ask the agent:

- Does the Grand Duke receive money from the government?
- Where does the Grand Duke reside?
- Can deputies submit bills?

## Agent Diagram

<img width="2750" height="696" alt="diagram" src="https://github.com/user-attachments/assets/55ce440b-41eb-4794-b931-cbfd4e247bb6" />


