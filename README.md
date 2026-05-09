# Syllabus-to-Study Agent

**An AI-Powered Academic Extraction Suite built for the AMD Developer Cloud Hackathon.**

## The Problem
Students spend hours at the start of every semester manually copying deadlines from messy PDF syllabi into their calendars and building flashcards for core concepts. 

## Our Solution
Omni-Syllabus-Agent automates the entire academic prep pipeline. Simply drop a syllabus PDF into our Streamlit app, and our dual-agent system takes over:
1. **The Calendar Agent:** Extracts every exam, quiz, and project deadline, instantly formatting them into a ready-to-import Google Calendar `.csv`.
2. **The Flashcard Agent:** Scans for core terminology and definitions, generating a ready-to-import Anki Deck.

## The Tech Stack (Hardware & Software)
We bypassed standard cloud APIs to build a fully local, privacy-first AI pipeline:
* **LLM Engine:** Open-weight `Meta-Llama-3-8B-Instruct`.
* **Hardware:** Deployed on an **AMD MI300X GPU** instance (192GB VRAM) via the AMD Developer Cloud.
* **Inference Server:** Dockerized environment running `vLLM` for high-throughput, low-latency API requests.
* **Frontend:** Built entirely in Python using `Streamlit`.

## Known Limitations & V2 Roadmap
**Current Limitation:** For this MVP, Llama 3 acts as our sole extraction engine. Because it is a text-only model, it relies on `PyPDF2` to scrape text, meaning it struggles with image-heavy or scanned syllabi.
**V2 Architecture:** We plan to implement a Multi-Agent system. We will deploy a Vision-Language Model (VLM) alongside Llama 3 to act as an OCR pre-processor, allowing the app to ingest any document format flawlessly.

---
*Note to Judges: This application relies on a live AMD MI300X GPU droplet. The backend inference server will remain active for the duration of the judging period.*
