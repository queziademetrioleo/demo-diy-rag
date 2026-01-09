#!/usr/bin/env python3
"""
Script 02: Save Knowledge Base

Creates and saves the knowledge base for quick reuse without reprocessing.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from simple_faq_rag import SimpleFAQSystem


def main():
    """Save the knowledge base."""

    print("="*70)
    print("💾 SAVING KNOWLEDGE BASE")
    print("="*70)

    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    csv_path = "data/faq_example.csv"
    output_path = "data/knowledge_base"

    if not project_id:
        print("❌ Configure PROJECT_ID in .env")
        return 1

    # Initialize
    print("\n1️⃣ Initializing system...")
    faq = SimpleFAQSystem(project_id=project_id)

    # Load CSV
    print("\n2️⃣ Loading CSV...")
    faq.load_csv(csv_path)

    # Create knowledge base
    print("\n3️⃣ Creating knowledge base...")
    print("⏳ Please wait... (1-2 minutes)")
    faq.create_knowledge_base()

    # Save
    print("\n4️⃣ Saving to file...")
    faq.save_knowledge_base(output_path)

    print("\n" + "="*70)
    print("✅ KNOWLEDGE BASE SAVED SUCCESSFULLY!")
    print("="*70)
    print("\nCreated files:")
    print(f"  - {output_path}_embeddings.npy")
    print(f"  - {output_path}_data.csv")
    print("\n💡 You can now load quickly with:")
    print(f"   faq.load_knowledge_base('{output_path}')")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
