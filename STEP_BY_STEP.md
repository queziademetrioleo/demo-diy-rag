# 🚀 Step-by-Step Guide - FAQ RAG System

**From Cloud Shell to a Working System in 15 Minutes**

This guide takes you from zero to a working intelligent FAQ system, without errors.

## 📋 Quick Index

1. [Prerequisites](#1-prerequisites)
2. [Cloud Shell and Project](#2-cloud-shell-and-project)
3. [Clone the Code](#3-clone-the-code)
4. [Enable APIs](#4-enable-apis)
5. [Create Bucket and Structure](#5-create-bucket-and-structure)
6. [Upload the CSV](#6-upload-the-csv)
7. [Configure .env](#7-configure-env-important)
8. [Install Dependencies](#8-install-dependencies)
9. [Process the FAQ](#9-process-the-faq)
10. [Run the Web Interface](#10-run-the-web-interface)

---

## 1. Prerequisites

**You need:**
- Google account (Gmail)
- Google Cloud project created
- Billing enabled (free tier works!)

**No local installs needed!** Everything runs in Cloud Shell (browser).

---

## 2. Cloud Shell and Project

### 2.1 Open Cloud Shell

1. Go to https://console.cloud.google.com
2. Click the **">_"** icon in the top right
3. The terminal window opens (Cloud Shell)

### 2.2 Configure the Project

```bash
# Check current project
gcloud config get-value project

# If missing or incorrect, set it:
gcloud config set project YOUR-PROJECT-ID

# Write down PROJECT_ID! You'll use it often.
```

**✅ Checkpoint:** `gcloud config get-value project` returns your project

---

## 3. Clone the Code

```bash
# Clone the repository
git clone https://github.com/queziademetrioleo/demo-diy-rag.git
cd demo-diy-rag

# Switch to the simple system branch
git checkout main-branch

# Verify files
ls -la
```

**You should see:**
- `simple_faq_rag.py` - RAG system
- `simple_gradio_app.py` - Gradio interface
- `simple_scripts/` - Helper scripts
- `data/faq_example.csv` - Example CSV
- `requirements.txt` - Dependencies

**✅ Checkpoint:** `simple_faq_rag.py` exists

---

## 4. Enable APIs

```bash
# Enable Vertex AI and Cloud Storage
gcloud services enable \
  aiplatform.googleapis.com \
  storage-api.googleapis.com

# Wait for activation (30 seconds)
sleep 30 && echo "✅ APIs enabled!"
```

**✅ Checkpoint:** Command finishes without errors

---

## 5. Create Bucket and Structure

### 5.1 Create Bucket

```bash
# Create bucket (automatically uses YOUR-PROJECT-ID)
gsutil mb -l us-central1 gs://$(gcloud config get-value project)-data
```

**⚠️ If you get "bucket exists":** That's okay. Continue.

### 5.2 Create Organized Folders

```bash
# Create folder structure in the bucket
echo "" | gsutil cp - gs://$(gcloud config get-value project)-data/raw_data/.keep
echo "" | gsutil cp - gs://$(gcloud config get-value project)-data/embeddings/.keep
echo "" | gsutil cp - gs://$(gcloud config get-value project)-data/knowledge_base/.keep

echo "✅ Structure created!"
```

**Structure created:**
```
your-project-data/
├── raw_data/          # Original CSV
├── embeddings/        # AI vectors (.npy)
└── knowledge_base/    # Metadata (.csv)
```

**✅ Checkpoint:** `gsutil ls gs://$(gcloud config get-value project)-data` shows the 3 folders

---

## 6. Upload the CSV

**⚠️ CRITICAL:** File name **MUST NOT** have spaces or special characters!

### Option A: Use the Example CSV (Recommended)

```bash
# Copy example CSV to bucket
gsutil cp data/faq_example.csv gs://$(gcloud config get-value project)-data/raw_data/
```

### Option B: Use Your Own CSV

**CSV rule:**
- At least **2 columns**
- **Column 1:** Questions (any name: Questions, Question, Q, etc.)
- **Column 2:** Answers (any name: Answers, Answer, A, etc.)

**STEP 1: Rename the file (if needed)**

If your file has spaces, rename it **before** uploading:

```bash
# Example: "FAQ - DEMO (v1).csv" → "faq_demo.csv"
# ❌ WRONG: file name with spaces breaks gsutil
# ✅ CORRECT: only letters, numbers, _ and -
```

**STEP 2: Upload via Cloud Shell**

1. Click the **⋮** menu (three dots) in Cloud Shell
2. Select **Upload**
3. Choose your CSV file (already renamed!)
4. Wait for "Upload completed"

**STEP 3: Copy to the bucket**

```bash
# Replace "faq_demo.csv" with your file name
gsutil cp ~/faq_demo.csv gs://$(gcloud config get-value project)-data/raw_data/
```

### Verify Upload

```bash
# List files in bucket
gsutil ls gs://$(gcloud config get-value project)-data/raw_data/

# It should show your CSV
```

**✅ Checkpoint:** Your CSV appears in the list

---

## 7. Configure .env (IMPORTANT!)

**⚠️ CRITICAL:** The .env file must NOT have decorative comments!

```bash
# Copy example
cp .env.example .env

# Edit
nano .env
```

**In the nano editor:**

1. Press `Ctrl+K` repeatedly until EVERYTHING is deleted
2. Paste EXACTLY this (replace YOUR-PROJECT-ID):

```bash
PROJECT_ID=YOUR-PROJECT-ID
LOCATION=us-central1
BUCKET_NAME=YOUR-PROJECT-ID-data
RAW_DATA_PATH=raw_data/faq_example.csv
```

**❌ DO NOT DO THIS:**
```bash
# ============================================
# CONFIGURATION (decorative comments!)
# ============================================
PROJECT_ID=...  # This breaks the parser!
```

**✅ DO THIS:**
```bash
PROJECT_ID=example-project-472216
LOCATION=us-central1
BUCKET_NAME=example-project-472216-data
RAW_DATA_PATH=raw_data/faq_example.csv
```

**If you used your own CSV, update `RAW_DATA_PATH`:**
```bash
RAW_DATA_PATH=raw_data/your_file.csv
```

**Save:**
1. `Ctrl+O` → `Enter`
2. `Ctrl+X`

**Check:**
```bash
cat .env
```

**✅ Checkpoint:** .env shows your 4 lines with no decorative comments

---

## 8. Install Dependencies

### 8.1 Create Virtual Environment

```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate
```

**Your prompt changes to:**
```
(venv) user@cloudshell:~/demo-diy-rag$
```

**⚠️ Important:** `(venv)` must appear. If not, run `source venv/bin/activate` again.

### 8.2 Install Packages

```bash
# Update pip
pip install --upgrade pip

# Install dependencies (~3 minutes)
pip install -r requirements.txt
```

**☕ Wait ~3 minutes...**

**Verify installation:**
```bash
pip list | grep google-cloud
```

**You should see:**
```
google-cloud-aiplatform    1.38.1
google-cloud-storage       2.14.0
```

**✅ Checkpoint:** Dependencies installed without errors

---

## 9. Process the FAQ

This script will:
1. Download the CSV from the bucket
2. Create embeddings with Vertex AI
3. Save the knowledge base to the bucket

```bash
# Run processing
python simple_scripts/03_use_bucket.py
```

**You will see:**

```
======================================================================
🪣 FAQ SYSTEM WITH GOOGLE CLOUD STORAGE
======================================================================

✅ Project: your-project-id
✅ Bucket: gs://your-project-data

======================================================================
STEP 1: Downloading data from Cloud Storage
======================================================================
📥 Downloading CSV from the bucket...
✅ Downloaded: [temporary file]

======================================================================
STEP 2: Initializing FAQ System
======================================================================
✅ System initialized!

======================================================================
STEP 3: Loading Questions and Answers
======================================================================
📊 Total questions: 25

======================================================================
STEP 4: Creating Knowledge Base (Embeddings)
======================================================================
⏳ This can take a few minutes...
```

**⏰ WAIT 2-5 MINUTES** - It is creating embeddings with AI!

**When it finishes:**

```
✅ Knowledge base created!

======================================================================
STEP 5: Saving Knowledge Base
======================================================================
✅ Embeddings saved
✅ Metadata saved

======================================================================
STEP 6: Uploading to Cloud Storage
======================================================================
📤 Uploading knowledge base...
   ✅ Embeddings uploaded
   ✅ Metadata uploaded

✅ Knowledge base saved in the bucket!

======================================================================
STEP 7: Testing System
======================================================================
🧪 Running 3 test questions:

[Tests appear here...]

======================================================================
✅ PROCESS COMPLETED SUCCESSFULLY!
======================================================================
```

**Verify it worked:**
```bash
# List created files
gsutil ls -r gs://$(gcloud config get-value project)-data/
```

**You should see:**
```
gs://your-project-data/embeddings/:
gs://your-project-data/embeddings/faq_embeddings.npy

gs://your-project-data/knowledge_base/:
gs://your-project-data/knowledge_base/faq_metadata.csv

gs://your-project-data/raw_data/:
gs://your-project-data/raw_data/faq_example.csv
```

**✅ Checkpoint:** 3 folders with created files

---

## 10. Run the Web Interface

### 10.1 Start Gradio

```bash
# Run Gradio app (simple!)
python simple_gradio_app.py
```

**You will see:**
```
💬 FAQ SYSTEM WITH AI - GRADIO
======================================================================

🚀 Loading FAQ from bucket: gs://your-project-data
📥 Downloading embeddings...
   ✅ 25 embeddings loaded
📥 Downloading metadata...
   ✅ 25 questions loaded
✅ FAQ system ready to use!

🌐 STARTING GRADIO SERVER
======================================================================

Running on local URL:  http://0.0.0.0:8080

To create a public link, set `share=True` in `launch()`.
```

### 10.2 Open in the Browser

**In Cloud Shell:**
1. Find the **"Web Preview"** button at the top
2. Click → **"Preview on port 8080"**
3. A new tab opens with the chat interface!

### 10.3 Use the System

**Gradio interface ready to use:**

1. **Modern chat** appears automatically
2. **Ready examples** to click:
   - "Hello!"
   - "How do I reset my password?"
   - "What's the delivery time?"
   - "Do you accept PIX?"

3. **Type your questions** in the text field
4. **Press Enter** or click "📤 Send"

**Interface features:**
- 💬 **Chat with history** (keeps conversation)
- 📊 **Metadata included** (confidence, score, source)
- 🔄 **Retry** (re-send message)
- ↩️ **Undo** (revert message)
- 🗑️ **Clear Conversation** (reset chat)
- 🎨 **Modern design** (Gradio Soft theme)

**✅ Checkpoint:** System answers correctly

**💡 Gradio is MUCH simpler:**
- ✅ No cache issues
- ✅ Auto-reload works better
- ✅ Only ~150 lines vs. 200+ for Streamlit
- ✅ Native chat UI (no custom implementation needed)

---

## 🎉 Congratulations!

You built a complete RAG system:
- ✅ Embeddings with Vertex AI
- ✅ LLM with Gemini
- ✅ Data organized in Cloud Storage
- ✅ Working web interface
- ✅ Prompt engineering + grounding
- ✅ Output filtering + safety

---

## Next Steps

### 1. Use Your Own CSV

Edit your CSV with real questions/answers, upload to the bucket (no spaces in name!), update `.env`, and run `03_use_bucket.py` again.

### 2. Customize Responses

Edit the prompt template in `simple_faq_rag.py:371` to change the tone.

### 3. Adjust Parameters

In `.env`, change:
- `TOP_K_RESULTS`: How many FAQs to retrieve (default: 3)
- `SIMILARITY_THRESHOLD`: How similar is required (default: 0.5)

### 4. Integrate Into Your System

```python
from simple_faq_rag import SimpleFAQSystem
import os
from dotenv import load_dotenv

load_dotenv()
faq = SimpleFAQSystem(project_id=os.getenv('PROJECT_ID'))

# Load from bucket
# (implement load_from_bucket if needed)

# Or load locally
faq.load_csv('your_faq.csv')
faq.embeddings = np.load('embeddings.npy')

# Use
result = faq.ask_with_llm("How do I create an account?")
print(result['generated_answer'])
```

---

## Summary of What Was Built

**Architecture:**
1. CSV → Cloud Storage (raw_data/)
2. Vertex AI creates embeddings (768 dimensions)
3. Embeddings saved in Cloud Storage (embeddings/)
4. Gradio auto-loads on start
5. User asks → Search similar embeddings → Gemini generates answer → Output filtering → Final answer

**Certification Requirements Met:**
- ✅ Prompt engineering (template with instructions)
- ✅ Chain-of-thought (optional, disabled)
- ✅ Grounding (answers based on FAQs)
- ✅ Output filtering (removes sensitive data)
- ✅ Safety settings (Gemini filters)
- ✅ Retrieval (embeddings + cosine similarity)
- ✅ Generation (Gemini 2.5 Flash)

---

## Estimated Costs

**For 1000 questions/month:**
- Embeddings: ~$0.05
- LLM: ~$0.10
- Storage: ~$0.02

**Total: ~$0.20/month**
