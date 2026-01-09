# 💬 Simple FAQ System with RAG

**DIY RAG demo for the Google Cloud Gen AI Services Specialization**

An intelligent FAQ system using **RAG (Retrieval Augmented Generation)** with:
- 🔍 **Embeddings** (Vertex AI text-embedding-004)
- 🤖 **LLM** (Gemini 2.5 Flash)
- ☁️ **Cloud Storage** (organized data buckets)
- 🎨 **Web Interface** (Gradio)

## 🎯 What This System Does

Answers user questions using an FAQ knowledge base:

1. **Retrieval:** Finds relevant FAQs using embeddings and cosine similarity
2. **Generation:** Gemini rewrites the answer naturally
3. **Output Filtering:** Removes sensitive information (emails, phone numbers, IDs)

**Example:**
```
User: "How do I reset my password?"
System:
  1. Finds similar FAQs (embeddings)
  2. Gemini generates an answer based on the retrieved FAQs
  3. Filters sensitive data before displaying
```

## 📁 Main Files

```
demo-diy-rag/
├── simple_faq_rag.py          # Full RAG system (embeddings + LLM)
├── simple_gradio_app.py       # Gradio UI (auto-loads from bucket)
├── requirements.txt           # Python dependencies
├── .env                       # Settings (do not commit!)
├── .env.example               # Configuration example
│
├── simple_scripts/
│   ├── 01_test_system.py      # Test the system locally
│   ├── 02_save_knowledge_base.py  # Save embeddings
│   └── 03_use_bucket.py       # Process CSV and upload to bucket
│
└── data/
    └── faq_example.csv        # Example CSV (Questions/Answers)
```

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Google Cloud project with billing enabled
- Cloud Shell (already includes Python 3.12, gcloud, etc.)

### Step 1: Clone and Configure

```bash
# In Cloud Shell
git clone https://github.com/your-user/demo-diy-rag.git
cd demo-diy-rag

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure .env

**IMPORTANT:** No decorative comments! Only `KEY=value`

```bash
# Copy example
cp .env.example .env

# Edit (use nano or Cloud Shell editor)
nano .env
```

`.env` content:
```bash
PROJECT_ID=your-project-id
LOCATION=us-central1
BUCKET_NAME=your-project-id-data
RAW_DATA_PATH=raw_data/faq_demo.csv
```

### Step 3: Create Bucket and Upload CSV

```bash
# Enable APIs
gcloud services enable aiplatform.googleapis.com storage-api.googleapis.com

# Create bucket
gsutil mb gs://your-project-id-data

# Upload the CSV (NO SPACES IN THE NAME!)
# Use Cloud Shell Editor (three dots > Upload) to upload your CSV
# Then:
gsutil cp ~/faq_demo.csv gs://your-project-id-data/raw_data/
```

**⚠️ COMMON ERROR:** File names with spaces break gsutil!
- ❌ WRONG: `FAC - DEMO1 (DIY RAG) - Page1.csv`
- ✅ CORRECT: `faq_demo.csv`

### Step 4: Process the FAQ and Create Embeddings

```bash
# Downloads CSV, creates embeddings, uploads to the bucket
python simple_scripts/03_use_bucket.py
```

This will:
- ✅ Download CSV from the bucket
- ✅ Create embeddings (text-embedding-004)
- ✅ Save to the bucket: `embeddings/faq_embeddings.npy` and `knowledge_base/faq_metadata.csv`

⏰ **Time:** ~5-10 minutes (depends on CSV size)

### Step 5: Run the Web Interface

```bash
# Gradio in Cloud Shell
python simple_gradio_app.py
```

The system automatically loads from the bucket (~10 seconds).

Click **"Web Preview"** (port 8080) in Cloud Shell to open the interface.

**Ready UI:** Modern chat with history, examples, and answer metadata.

## 📊 CSV Format

**Simple rule:** The system uses the **first 2 columns** of the CSV:
- **Column 1 (index 0):** Questions
- **Column 2 (index 1):** Answers

**Column names can be ANYTHING!**

**Examples that work:**

```csv
Questions,Answers
"How to reset password?","Go to Settings > Account > Reset Password..."
```

```csv
question,answer
"How to reset password?","Go to Settings > Account > Reset Password..."
```

```csv
Q,A
"What?","This..."
```

```csv
question_text,answer_text
"Help?","Sure..."
```

All work! The system just reads: 1st column = question, 2nd = answer.

## 🏗️ Architecture

```
┌─────────────────┐
│   CSV FAQ       │  ← Questions and Answers
│  (Cloud Storage)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vertex AI       │  ← Create embeddings (768D vectors)
│ text-embedding  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Embeddings     │  ← Saved in bucket
│ (.npy + .csv)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Gradio App    │  ← Auto-loads on startup
│ (simple_gradio  │
│    _app.py)     │
└────────┬────────┘
         │
    User Query
         │
         ▼
┌─────────────────┐
│   RETRIEVAL     │  ← Similarity search (cosine)
│  (Top 3 FAQs)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   GENERATION    │  ← Gemini rewrites answer
│ (Gemini 2.5)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OUTPUT FILTER   │  ← Removes sensitive data
│  (Regex)        │
└────────┬────────┘
         │
         ▼
    📤 Answer
```

## 🔧 Technologies

| Component | Technology | Why | 
|----------|------------|-----|
| **Embeddings** | Vertex AI text-embedding-004 | 768 dimensions, SOTA performance |
| **LLM** | Gemini 2.5 Flash | Fast, cost-effective, high quality |
| **Search** | scikit-learn cosine_similarity | Simple, no Vector Search infra |
| **Storage** | Cloud Storage | Organized, scalable |
| **Interface** | Gradio | Simple (60 lines), native chat, auto-reload |
| **Python** | 3.12 (Cloud Shell) | Default environment version |

## ✅ Certification Requirements

This project meets all **Demo #1** requirements:

- [x] **Prompt Engineering:** Template with grounding instructions
- [x] **Chain-of-Thought:** Optional via parameter (disabled by default)
- [x] **Grounding:** Answers based only on retrieved FAQs
- [x] **Output Filtering:** Removes emails, phone numbers, IDs
- [x] **Safety Settings:** Block harmful content (Gemini safety filters)
- [x] **Retrieval:** Embeddings + cosine similarity
- [x] **Generation:** Gemini 2.5 Flash
- [x] **Cloud Storage:** Data organized in buckets

## 🐛 Common Errors and Fixes

### 1. Error: `CommandException: No URLs matched`
**Cause:** File name contains spaces
**Fix:** Rename file without spaces/special characters

```bash
# If the file is already in the bucket with spaces, rename it:
python
from google.cloud import storage
client = storage.Client()
bucket = client.bucket("your-bucket")
blob = bucket.blob("raw_data/file with spaces.csv")
bucket.copy_blob(blob, bucket, "raw_data/file_without_spaces.csv")
blob.delete()
```

### 2. Error: `python-dotenv could not parse statement`
**Cause:** Decorative comments in .env
**Fix:** Remove all decorative comments!

❌ **WRONG:**
```bash
# ============================================
# CONFIGURATION
# ============================================
PROJECT_ID=my-project
```

✅ **CORRECT:**
```bash
PROJECT_ID=my-project
LOCATION=us-central1
BUCKET_NAME=my-bucket
```

### 3. Error: `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`
**Cause:** numpy incompatible with Python 3.12
**Fix:** Already fixed in requirements.txt (numpy>=1.26.0)

### 4. Git push returns 403
**Cause:** Branch without `claude/` prefix
**Fix:**
```bash
git checkout -b claude/your-feature-34uUC
git push -u origin claude/your-feature-34uUC
```

## 📚 More Information

- **Detailed step-by-step guide:** `STEP_BY_STEP.md`
- **Legacy documentation (reference):** `archive/`

## 💰 Estimated Costs

For 1000 questions/month:

- Embeddings: ~$0.05 (text-embedding-004)
- LLM Generation: ~$0.10 (Gemini 2.5 Flash)
- Cloud Storage: ~$0.02 (few MB)

**Total:** ~$0.20/month (approx.)

## 🎓 About the Certification

This project was built for:
**Google Cloud Gen AI Services Specialization - Demo #1**

Requirements met:
- ✅ Original code documented
- ✅ Dataset in Cloud Storage
- ✅ Clear business goal (intelligent FAQ)
- ✅ Full RAG (Retrieval + Generation)
- ✅ Prompt engineering
- ✅ Output filtering and safety

## 📞 Support

**Issues:** Open an issue in this repository
**Google Cloud Docs:** https://cloud.google.com/vertex-ai/docs

---

**Built for Google Cloud Gen AI Services Specialization** 🚀
