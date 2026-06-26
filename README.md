# 🎨 BrailleArt AI

BrailleArt AI is a multi-agent AI system that makes artwork accessible for visually impaired users. It analyzes paintings and images, understands their visual and historical context, and generates accessible descriptions, Braille representations, and learning resources.

This project is being developed for **Kaggle's AI Agents: Intensive Vibe Coding Capstone** under the **Agents for Good** track.

---

## ✨ Features

* 🤖 Multi-Agent Architecture using Google ADK
* 👁️ Vision Analysis
* 🔍 OCR Text Extraction
* 🎨 Art Knowledge & Context
* 😊 Emotion & Symbolism Analysis
* ♿ Accessibility Report Generation
* ⠿ Braille Conversion
* 📚 Educational Learning Support
* 🔒 Secure File Processing
* 📦 FastAPI Backend
* 🎨 Streamlit Frontend
* 🔌 MCP Integration

---

## 🛠️ Tech Stack

* Python
* Google ADK
* Gemini 2.5 Flash
* FastAPI
* Streamlit
* SQLite
* FastMCP
* Docker

---

## 📂 Project Structure

```text
BrailleArt-AI/
├── src/
│   ├── agents/
│   ├── backend/
│   ├── frontend/
│   ├── database/
│   ├── mcp/
│   ├── tools/
│   └── utils/
├── tests/
├── README.md
├── requirements.txt
└── Dockerfile
```

---

## 🚀 Getting Started

```bash
git clone https://github.com/<your-username>/BrailleArt-AI.git
cd BrailleArt-AI

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key
```

Run the backend:

```bash
uvicorn src.backend.main:app --reload
```

Run the frontend:

```bash
streamlit run src/frontend/app.py
```

---

## 📌 Current Progress

### ✅ Completed

* Planner Agent
* Orchestrator Agent
* Vision Agent
* OCR Agent
* Art Knowledge Agent
* Emotion Agent
* Accessibility Agent

### 🚧 In Progress

* Braille Agent
* Tactile Layout Agent
* Evaluation Agent
* Reflection Agent
* Conversation Agent
* Learning Agent
* Explainability Agent
* Streamlit UI
* FastAPI Integration
* MCP Servers
* Deployment

---

## 📖 Project Status

This project is currently under active development. Features, architecture, and documentation will continue to evolve as development progresses.
