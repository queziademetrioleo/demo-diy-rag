"""
🤖 Simple FAQ System with RAG

A simplified system for finding answers in a CSV using AI.

How it works:
1. You have a CSV with questions and answers
2. The system turns questions into vectors (embeddings)
3. When you ask a question, it finds the most similar one
4. Returns the corresponding answer

No unnecessary complexity. Simple semantic search with optional LLM.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import aiplatform
from google.cloud import storage
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity
import json
import re
from vertexai.generative_models import GenerativeModel, GenerationConfig, HarmCategory, HarmBlockThreshold


class SimpleFAQSystem:
    """
    Simple FAQ system with semantic search.

    Uses an LLM to generate a natural answer grounded in retrieved FAQs.
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        csv_path: Optional[str] = None
    ):
        """
        Initialize the FAQ system.

        Args:
            project_id: Google Cloud project ID
            location: Region (default: us-central1)
            csv_path: Path to the CSV with questions/answers
        """
        self.project_id = project_id
        self.location = location
        self.csv_path = csv_path

        # Data
        self.df = None  # DataFrame with questions/answers
        self.embeddings = None  # Question vectors

        # Initialize Vertex AI
        logger.info("Initializing Vertex AI...")
        vertexai.init(project=project_id, location=location)
        aiplatform.init(project=project_id, location=location)

        # Embedding model
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

        # LLM model for generation (Gemini)
        self.llm_model = GenerativeModel("gemini-2.5-flash")

        # LLM configuration
        self.generation_config = GenerationConfig(
            temperature=0.2,  # Lower temperature for more consistent answers
            top_p=0.8,
            top_k=40,
            max_output_tokens=1024,
        )

        logger.info("✅ FAQ system initialized (with LLM)!")

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load CSV with questions and answers.

        Uses the first two columns of the CSV:
        - Column 0: Questions (any name: Questions, Question, Q, etc.)
        - Column 1: Answers (any name: Answers, Answer, A, etc.)

        Args:
            csv_path: Path to the CSV file (minimum 2 columns)

        Returns:
            DataFrame with standardized columns ('question', 'answer', 'id')
        """
        logger.info(f"📂 Loading CSV: {csv_path}")

        df = pd.read_csv(csv_path)

        # Validate that it has at least 2 columns
        if len(df.columns) < 2:
            raise ValueError(
                "CSV must have at least 2 columns (questions and answers). "
                f"Found: {len(df.columns)} column(s)"
            )

        # Get names of the first two columns
        question_col = df.columns[0]
        answer_col = df.columns[1]

        logger.info(f"📊 Using columns: '{question_col}' (questions) | '{answer_col}' (answers)")

        # Create standardized DataFrame
        # Uses the first two columns regardless of name
        standardized_df = pd.DataFrame({
            'question': df.iloc[:, 0],  # First column
            'answer': df.iloc[:, 1]   # Second column
        })

        # Remove empty rows
        standardized_df = standardized_df.dropna(subset=['question', 'answer'])

        # Add ID
        standardized_df['id'] = [f"FAQ_{i:04d}" for i in range(len(standardized_df))]

        self.df = standardized_df

        logger.info(f"✅ {len(standardized_df)} questions loaded")
        return standardized_df

    def generate_embeddings(self, texts: List[str], batch_size: int = 250) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts
            batch_size: Batch size (max 250)

        Returns:
            Numpy array with embeddings
        """
        logger.info(f"🔄 Generating embeddings for {len(texts)} texts...")

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Create inputs
            inputs = [
                TextEmbeddingInput(text=text, task_type="RETRIEVAL_DOCUMENT")
                for text in batch
            ]

            # Generate embeddings
            batch_embeddings = self.embedding_model.get_embeddings(inputs)
            batch_vectors = [emb.values for emb in batch_embeddings]

            embeddings.extend(batch_vectors)

            logger.info(f"  Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

        embeddings_array = np.array(embeddings, dtype=np.float32)

        logger.info(f"✅ Embeddings generated: {embeddings_array.shape}")

        return embeddings_array

    def create_knowledge_base(self):
        """
        Create the knowledge base by generating embeddings for all questions.

        This must be run ONCE before searching.
        """
        if self.df is None:
            raise ValueError("CSV not loaded! Run load_csv() first.")

        logger.info("🧠 Creating knowledge base...")

        # Generate embeddings for questions
        questions = self.df['question'].tolist()
        self.embeddings = self.generate_embeddings(questions)

        logger.info("✅ Knowledge base created!")

    def search(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search for questions similar to the query.

        Args:
            query: User question
            top_k: How many answers to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of dictionaries with question, answer, and score
        """
        if self.embeddings is None:
            raise ValueError(
                "Knowledge base not created! "
                "Run create_knowledge_base() first."
            )

        logger.info(f"🔍 Searching: '{query}'")

        # Generate embedding for the query
        query_input = TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")
        query_emb = self.embedding_model.get_embeddings([query_input])[0]
        query_vector = np.array(query_emb.values, dtype=np.float32).reshape(1, -1)

        # Compute similarity with all questions
        similarities = cosine_similarity(query_vector, self.embeddings)[0]

        # Get top K
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Build results
        results = []
        for idx in top_indices:
            score = float(similarities[idx])

            # Filter by threshold
            if score < threshold:
                continue

            results.append({
                'id': self.df.iloc[idx]['id'],
                'question': self.df.iloc[idx]['question'],
                'answer': self.df.iloc[idx]['answer'],
                'score': score,
                'confidence': self._score_to_confidence(score)
            })

        logger.info(f"✅ Found {len(results)} answers above threshold")

        return results

    def ask(self, query: str) -> Dict:
        """
        Ask a question and return the best answer.

        This is the main method for simple usage.

        Args:
            query: Your question

        Returns:
            Dictionary with answer, score, etc.
        """
        results = self.search(query, top_k=1)

        if not results:
            return {
                'question_found': None,
                'answer': "Sorry, I couldn't find an answer for that question.",
                'score': 0.0,
                'confidence': 'low',
                'found': False
            }

        best = results[0]
        return {
            'question_found': best['question'],
            'answer': best['answer'],
            'score': best['score'],
            'confidence': best['confidence'],
            'found': True
        }

    def ask_with_llm(self, query: str, use_chain_of_thought: bool = False) -> Dict:
        """
        Ask a question and return a GENERATED answer from the LLM (full RAG).

        This implements full RAG:
        1. Retrieval: Find relevant FAQs (embeddings)
        2. Generation: LLM generates an answer based on retrieved FAQs

        Args:
            query: User question
            use_chain_of_thought: If True, uses chain-of-thought prompting

        Returns:
            Dictionary with generated answer, score, etc.
        """
        logger.info(f"🤖 Processing with LLM: '{query}'")

        # STEP 1: RETRIEVAL - Find relevant FAQs
        retrieval_results = self.search(query, top_k=3, threshold=0.5)

        if not retrieval_results:
            return {
                'user_question': query,
                'question_found': None,
                'original_answer': None,
                'generated_answer': "Sorry, I couldn't find relevant information about that question in our knowledge base.",
                'score': 0.0,
                'confidence': 'low',
                'found': False,
                'method': 'llm',
                'grounded': False
            }

        # Take top 3 for context
        context_faqs = retrieval_results[:3]

        # STEP 2: GENERATION - Build prompt and generate answer
        prompt = self._create_prompt(
            user_query=query,
            context_faqs=context_faqs,
            use_chain_of_thought=use_chain_of_thought
        )

        # Generate answer with LLM
        generated_response = self._generate_with_gemini(prompt)

        # STEP 3: OUTPUT FILTERING - Filter output
        filtered_response = self._filter_output(generated_response)

        # Best match for reference
        best_match = context_faqs[0]

        return {
            'user_question': query,
            'question_found': best_match['question'],
            'original_answer': best_match['answer'],
            'generated_answer': filtered_response,
            'score': best_match['score'],
            'confidence': best_match['confidence'],
            'found': True,
            'method': 'llm',
            'grounded': True,  # Answer is grounded in retrieved FAQs
            'num_sources': len(context_faqs)
        }

    def _create_prompt(
        self,
        user_query: str,
        context_faqs: List[Dict],
        use_chain_of_thought: bool = False
    ) -> str:
        """
        Create a prompt template for the LLM with grounding.

        Implements:
        - Prompt engineering
        - Grounding in real FAQs
        - Chain-of-thought (optional)
        """

        # Build context from retrieved FAQs
        context_text = ""
        for i, faq in enumerate(context_faqs, 1):
            context_text += f"\n[FAQ {i}]\n"
            context_text += f"Question: {faq['question']}\n"
            context_text += f"Answer: {faq['answer']}\n"
            context_text += f"Relevance: {faq['score']:.0%}\n"

        if use_chain_of_thought:
            # Chain-of-thought prompting
            prompt = f"""You are a specialized FAQ assistant. Answer the user's question following this process:

1. ANALYSIS: Analyze the user's question and identify which FAQ is most relevant.
2. REASONING: Briefly explain why this FAQ answers the question.
3. ANSWER: Provide the final answer clearly and directly.

CONTEXT (FAQs found in our database):
{context_text}

USER'S QUESTION:
{user_query}

IMPORTANT INSTRUCTIONS:
- Use ONLY information from the FAQs above
- If the question cannot be answered with the FAQs, say so clearly
- Be concise and direct
- Maintain a professional and helpful tone

ANSWER (follow format 1-2-3):"""

        else:
            # Default prompt (more direct)
            prompt = f"""You are a specialized and helpful FAQ assistant. Your role is to answer questions using ONLY the information from the provided knowledge base.

KNOWLEDGE BASE (relevant FAQs):
{context_text}

USER'S QUESTION:
{user_query}

INSTRUCTIONS:
- If the user only greets (hello, hi, good morning, etc.) WITHOUT asking a specific question:
  * Greet back in a friendly way
  * Introduce yourself as an FAQ assistant
  * Encourage them to ask a question: "How can I help? Ask your question!"
  * DO NOT say you didn't find information

- If the user asks a real question:
  * Use ONLY the information from the FAQs above
  * If the FAQs don't answer the question, say: "I couldn't find specific information about that in our knowledge base"
  * Be clear, direct, and helpful
  * Rephrase the FAQ answer naturally, don't copy exactly

ANSWER:"""

        return prompt

    def _generate_with_gemini(self, prompt: str) -> str:
        """
        Generate a response using Gemini LLM.

        Args:
            prompt: Formatted prompt

        Returns:
            Generated response
        """
        try:
            response = self.llm_model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )

            generated_text = response.text

            logger.info("✅ Response generated by LLM")

            return generated_text

        except Exception as e:
            logger.error(f"❌ Error generating with LLM: {e}")
            return "Sorry, an error occurred while processing your question. Please try again."

    def _filter_output(self, text: str) -> str:
        """
        Filter output to remove potentially problematic content.

        Implements basic output filtering:
        - Removes sensitive information (emails, phone numbers, IDs)
        - Removes inappropriate language
        - Limits size
        """

        # Remove emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REMOVED]', text)

        # Remove phone numbers (BR format)
        text = re.sub(r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}', '[PHONE_REMOVED]', text)

        # Remove CPF-like IDs
        text = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', '[ID_REMOVED]', text)

        # Limit size
        max_chars = 2000
        if len(text) > max_chars:
            text = text[:max_chars] + "... [response truncated]"

        # List of forbidden words (basic example)
        forbidden_words = ['[forbidden_word_example]']  # Add as needed
        for word in forbidden_words:
            text = text.replace(word, '[CONTENT_FILTERED]')

        return text.strip()

    def _score_to_confidence(self, score: float) -> str:
        """Convert numeric score into text."""
        if score >= 0.9:
            return 'very high'
        elif score >= 0.8:
            return 'high'
        elif score >= 0.7:
            return 'medium'
        else:
            return 'low'

    def save_knowledge_base(self, output_path: str):
        """
        Save the knowledge base to files.

        Args:
            output_path: Path to save (without extension)
        """
        if self.embeddings is None or self.df is None:
            raise ValueError("Knowledge base not created!")

        logger.info("💾 Saving knowledge base...")

        # Save embeddings
        np.save(f"{output_path}_embeddings.npy", self.embeddings)

        # Save DataFrame
        self.df.to_csv(f"{output_path}_data.csv", index=False)

        logger.info(f"✅ Saved to: {output_path}")

    def load_knowledge_base(self, input_path: str):
        """
        Load a saved knowledge base.

        Args:
            input_path: Base path (without extension)
        """
        logger.info("📂 Loading knowledge base...")

        # Load embeddings
        self.embeddings = np.load(f"{input_path}_embeddings.npy")

        # Load DataFrame
        self.df = pd.read_csv(f"{input_path}_data.csv")

        logger.info(f"✅ Base loaded: {len(self.df)} questions")

    def get_stats(self) -> Dict:
        """Return knowledge base statistics."""
        if self.df is None:
            return {"status": "No data loaded"}

        return {
            'total_questions': len(self.df),
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else None,
            'knowledge_base_created': self.embeddings is not None,
            'memory_size_mb': self.embeddings.nbytes / 1024 / 1024 if self.embeddings is not None else 0
        }


def demo():
    """Demonstration of system usage."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("="*60)
    print("🤖 DEMO - Simple FAQ System")
    print("="*60)

    # Configure
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("❌ Configure PROJECT_ID in .env")
        return

    # Initialize system
    print("\n1️⃣ Initializing system...")
    faq = SimpleFAQSystem(project_id=project_id)

    # Load CSV (you need one!)
    csv_path = "data/faq_example.csv"
    if not Path(csv_path).exists():
        print(f"❌ CSV not found: {csv_path}")
        print("Create a CSV with 'question' and 'answer' columns")
        return

    print("\n2️⃣ Loading CSV...")
    faq.load_csv(csv_path)

    print("\n3️⃣ Creating knowledge base...")
    faq.create_knowledge_base()

    print("\n4️⃣ Running test questions...")

    test_queries = [
        "How do I reset my password?",
        "What is the delivery time?",
        "How do I cancel an order?"
    ]

    for query in test_queries:
        print(f"\n❓ Question: {query}")
        result = faq.ask(query)

        if result['found']:
            print(f"✅ Answer ({result['confidence']} confidence):")
            print(f"   {result['answer']}")
            print(f"   Score: {result['score']:.2%}")
        else:
            print("❌ Answer not found")

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("="*60)


if __name__ == "__main__":
    demo()
