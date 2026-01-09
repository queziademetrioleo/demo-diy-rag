#!/usr/bin/env python3
"""
Script 01: Test Simple FAQ System

This script tests the FAQ system interactively.
It is the easiest way to get started!
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from simple_faq_rag import SimpleFAQSystem


def main():
    """Test the FAQ system."""

    print("="*70)
    print("🤖 SIMPLE FAQ SYSTEM TEST")
    print("="*70)

    # Load configuration
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("\n❌ ERROR: PROJECT_ID not configured in .env")
        print("\n📝 How to fix:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("2. Edit .env and fill PROJECT_ID")
        return 1

    print(f"\n✅ Project: {project_id}")

    # Check CSV
    csv_path = "data/faq_example.csv"
    if not Path(csv_path).exists():
        print(f"\n❌ ERROR: CSV not found: {csv_path}")
        print("\n💡 Use the example CSV included in the project!")
        return 1

    print(f"✅ CSV found: {csv_path}")

    # Initialize system
    print("\n" + "="*70)
    print("STEP 1: Initializing system...")
    print("="*70)

    try:
        faq = SimpleFAQSystem(project_id=project_id)
        print("✅ System initialized!")
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        print("\n💡 Make sure you are authenticated:")
        print("   gcloud auth application-default login")
        return 1

    # Load CSV
    print("\n" + "="*70)
    print("STEP 2: Loading questions and answers...")
    print("="*70)

    try:
        faq.load_csv(csv_path)
        stats = faq.get_stats()
        print(f"✅ {stats['total_questions']} questions loaded!")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return 1

    # Create knowledge base
    print("\n" + "="*70)
    print("STEP 3: Creating knowledge base...")
    print("="*70)
    print("⏳ Generating embeddings... (may take 1-2 minutes)")

    try:
        faq.create_knowledge_base()
        print("✅ Knowledge base created!")
    except Exception as e:
        print(f"❌ Error creating knowledge base: {e}")
        print("\n💡 Make sure the API is enabled:")
        print("   gcloud services enable aiplatform.googleapis.com")
        return 1

    # Test questions
    print("\n" + "="*70)
    print("STEP 4: Testing questions...")
    print("="*70)

    test_questions = [
        "How do I reset my password?",
        "How long does delivery take?",
        "Can I return an order?",
        "Do you accept PIX?"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}/{len(test_questions)}")
        print(f"❓ Question: {question}")

        try:
            result = faq.ask(question)

            if result['found']:
                print(f"✅ Answer found (confidence: {result['confidence']})")
                print(f"💬 {result['answer']}")
                print(f"📊 Score: {result['score']:.1%}")
                print(f"🔗 Original question: {result['question_found']}")
            else:
                print("❌ No answer found")

        except Exception as e:
            print(f"❌ Error: {e}")

    # Interactive mode
    print("\n" + "="*70)
    print("INTERACTIVE MODE - Ask your questions!")
    print("="*70)
    print("Type 'exit' to quit\n")

    while True:
        try:
            question = input("❓ Your question: ").strip()

            if not question:
                continue

            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break

            result = faq.ask(question)

            if result['found']:
                print(f"\n💬 Answer (confidence: {result['confidence']}):")
                print(f"   {result['answer']}")
                print(f"   Score: {result['score']:.1%}\n")
            else:
                print("\n❌ Sorry, I couldn't find an answer for that.\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

    print("\n" + "="*70)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\n📚 Next steps:")
    print("1. Use your own CSV with Questions/Answers")
    print("2. Run: python simple_scripts/02_save_knowledge_base.py")
    print("3. Then: python simple_gradio_app.py")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
