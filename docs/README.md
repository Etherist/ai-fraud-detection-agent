# Documentation Index

Welcome to the AI Fraud Detection Agent documentation.

---

## 📑 Document Index

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](../README.md) | Project overview, features, installation | Everyone |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide | New users |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete build summary & handover | Developers/employers |
| [VERIFICATION.md](VERIFICATION.md) | Final verification checklist & test results | QA/Reviewers |
| [architecture.md](architecture.md) | System design, agent specs, data flow | Architects |
| [agent_workflow.md](agent_workflow.md) | Agent orchestration, collaboration patterns | Software engineers |
| [api_reference.md](api_reference.md) | REST API endpoints, models, examples | API consumers |
| [apra_compliance.md](apra_compliance.md) | APRA APS 222 alignment details | Compliance officers |
| [data_format.md](data_format.md) | File format specifications, validation | Data engineers |
| [demo_guide.md](demo_guide.md) | Step-by-step demo instructions | Presenters/Demo |

---

## 🗺️ Documentation Structure

```
docs/
├── 📄 README.md               ← This index
├── 🚀 QUICKSTART.md           ← 5-minute setup
├── 📋 PROJECT_SUMMARY.md      ← Build checklist & features
├── ✅ VERIFICATION.md          ← Final verification checklist
├── 🏗️ architecture.md         ← System design (Mermaid diagrams)
├── 🤖 agent_workflow.md       ← Agent orchestration deep dive
├── 🌐 api_reference.md        ← FastAPI endpoint documentation
├── 🇦🇺 apra_compliance.md     ← APS 222 regulatory alignment
├── 📊 data_format.md          ← CSV/PDF input specifications
└── 🎬 demo_guide.md           ← Step-by-step demo walkthrough
```

---

## 🎯 Getting Started Paths

### "I want to run the demo"
→ Start with **QUICKSTART.md**

### "I want to understand the system architecture"
→ Read **architecture.md**

### "I want to extend an agent"
→ See **agent_workflow.md** + code in `src/agents/`

### "I want to call the API"
→ See **api_reference.md** + `/docs` endpoint (Swagger UI)

### "I need to ensure APRA compliance"
→ See **apra_compliance.md**

### "I need to know what CSV format to upload"
→ See **data_format.md**

### "I'm evaluating this for my team"
→ Read **README.md** + **PROJECT_SUMMARY.md** + **VERIFICATION.md**

---

## 📖 Recommended Reading Order

1. **README.md** – high-level project understanding
2. **QUICKSTART.md** – get it running locally in 5 minutes
3. **architecture.md** – system design overview with diagrams
4. **agent_workflow.md** – deep dive into agent interactions
5. **api_reference.md** – integration details (if building on API)
6. **apra_compliance.md** – regulatory alignment (if compliance-focused)
7. **demo_guide.md** – customization & presentation tips
8. **PROJECT_SUMMARY.md** – full feature matrix & build details
9. **VERIFICATION.md** – final validation checklist

---

## 📚 Additional Resources

- **Code Documentation:** Each agent has inline docstrings (PEP 257)
- **Type Hints:** Full typing coverage (PEP 484)
- **Tests:** `tests/` folder shows usage examples (110 tests, 100% pass)
- **Notebook:** `notebooks/demo.ipynb` – interactive walkthrough
- **API Docs:** `http://localhost:8000/docs` (Swagger UI) when server running
- **ReDoc:** `http://localhost:8000/redoc`

---

*Documentation maintained alongside code. Last updated: 2026-04-28*
