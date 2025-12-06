"""
Question decomposition module for breaking down complex questions into sub-questions.
This is the foundation for multi-step reasoning in the agent system.
"""
import os
import json
from typing import List, Dict, Optional
from backend.config import (
    LLM_PROVIDER, LLM_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL
)


DECOMPOSE_PROMPT = """You are an expert at breaking down complex questions about codebases into smaller, focused sub-questions.

Your task is to analyze a complex question and decompose it into 3-7 sub-questions that can be answered individually.
Each sub-question should be:
1. Specific and focused (can be answered with a targeted search)
2. Actionable (clearly indicates what to search for)
3. Logical (builds understanding step by step)
4. Complete (together they answer the original question)

Guidelines:
- If the question is already simple, return 1-2 sub-questions
- If the question is very complex, break it into 5-7 sub-questions
- Order sub-questions logically (foundational concepts first)
- Each sub-question should be a complete, standalone question

Example 1:
Question: "How does authentication work in this codebase?"
Sub-questions:
1. Where is user login handled?
2. What authentication methods are used (JWT, sessions, etc.)?
3. How are authentication tokens generated and validated?
4. Where are protected routes defined?
5. How is user session managed?

Example 2:
Question: "What is the main structure of this project?"
Sub-questions:
1. What is the overall project type (web app, API, library)?
2. What are the main directories and their purposes?
3. What are the core modules and their responsibilities?
4. What are the key entry points (main files, routes, etc.)?

Now decompose this question:

Question: {question}

Return your response as a JSON array of strings, where each string is a sub-question.
Format: ["sub-question 1", "sub-question 2", ...]
"""


def decompose_question(question: str, model: Optional[str] = None, temperature: float = 0.3) -> List[str]:
    """
    Decompose a complex question into smaller sub-questions.
    
    Args:
        question: The original complex question
        model: Optional model override
        temperature: Sampling temperature (0.3 for focused decomposition)
    
    Returns:
        List of sub-questions (strings)
    """
    if not question or not question.strip():
        return [question] if question else []
    
    # Simple questions don't need decomposition
    # Check if question seems complex enough
    question_lower = question.lower()
    simple_indicators = ["what is", "where is", "show me", "find"]
    is_likely_simple = any(question_lower.startswith(indicator) for indicator in simple_indicators) and len(question.split()) < 10
    
    if is_likely_simple and "how" not in question_lower and "why" not in question_lower:
        print(f"[decomposer] Question appears simple, returning as-is")
        return [question]
    
    # Build prompt
    prompt = DECOMPOSE_PROMPT.format(question=question)
    
    # Model selection
    if model:
        model_to_use = model
    elif os.getenv("LLM_MODEL"):
        model_to_use = os.getenv("LLM_MODEL")
    elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
        model_to_use = os.getenv("OPENAI_MODEL")
    else:
        model_to_use = LLM_MODEL
    
    # Get LLM response
    try:
        # Handle Anthropic separately
        if LLM_PROVIDER == "anthropic":
            from anthropic import Anthropic
            anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
            message = anthropic_client.messages.create(
                model=model_to_use,
                max_tokens=1024,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
        else:
            # OpenAI-compatible providers
            from openai import OpenAI
            
            # Get client
            if LLM_PROVIDER == "deepseek":
                api_key = DEEPSEEK_API_KEY or OPENAI_API_KEY
                base_url = DEEPSEEK_BASE_URL if DEEPSEEK_API_KEY else (OPENAI_BASE_URL or DEEPSEEK_BASE_URL)
                client = OpenAI(api_key=api_key, base_url=base_url)
            elif LLM_PROVIDER == "openai":
                client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
            elif LLM_PROVIDER == "qwen":
                api_key = QWEN_API_KEY or OPENAI_API_KEY
                base_url = QWEN_BASE_URL or OPENAI_BASE_URL
                client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            else:
                api_key = DEEPSEEK_API_KEY or OPENAI_API_KEY
                base_url = DEEPSEEK_BASE_URL
                client = OpenAI(api_key=api_key, base_url=base_url)
            
            rsp = client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            response_text = rsp.choices[0].message.content
        
        # Parse JSON response
        # Try to extract JSON array from response (might have extra text)
        response_text = response_text.strip()
        
        # Find JSON array in response
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            try:
                sub_questions = json.loads(json_str)
                if isinstance(sub_questions, list) and all(isinstance(q, str) for q in sub_questions):
                    print(f"[decomposer] Decomposed into {len(sub_questions)} sub-questions")
                    return sub_questions
            except json.JSONDecodeError:
                pass
        
        # Fallback: Try to extract questions from text format
        # Look for numbered list or bullet points
        lines = response_text.split('\n')
        questions = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove numbering/bullets
            line = line.lstrip('1234567890.-* ')
            # Check if it looks like a question
            if line and ('?' in line or line.startswith(('What', 'How', 'Where', 'Why', 'When', 'Which', 'Who'))):
                questions.append(line.rstrip('.'))
        
        if questions:
            print(f"[decomposer] Extracted {len(questions)} sub-questions from text format")
            return questions
        
        # Last resort: return original question
        print(f"[decomposer] Could not parse response, returning original question")
        return [question]
        
    except Exception as e:
        print(f"[decomposer] Error decomposing question: {e}")
        # On error, return original question
        return [question]


def is_complex_question(question: str) -> bool:
    """
    Heuristic to determine if a question is complex enough to warrant decomposition.
    
    Args:
        question: The question to check
    
    Returns:
        True if question appears complex, False otherwise
    """
    if not question:
        return False
    
    question_lower = question.lower()
    
    # Indicators of complexity
    complexity_indicators = [
        "how does", "how do", "how are", "how is",
        "explain", "describe", "analyze", "compare",
        "what is the structure", "what are the components",
        "walk me through", "guide me through",
        "multiple", "several", "all", "various"
    ]
    
    # Multiple clauses or conjunctions
    has_conjunctions = any(word in question_lower for word in ["and", "or", "but", "also", "then"])
    
    # Question length
    is_long = len(question.split()) > 10
    
    # Has complexity indicators
    has_indicators = any(indicator in question_lower for indicator in complexity_indicators)
    
    return has_indicators or (is_long and has_conjunctions)


def analyze_decomposition(question: str, sub_questions: List[str]) -> Dict:
    """
    Analyze the quality of a question decomposition.
    
    Args:
        question: Original question
        sub_questions: List of decomposed sub-questions
    
    Returns:
        Dict with analysis metrics
    """
    return {
        "original_question": question,
        "sub_questions_count": len(sub_questions),
        "avg_sub_question_length": sum(len(q.split()) for q in sub_questions) / len(sub_questions) if sub_questions else 0,
        "decomposition_ratio": len(sub_questions) / len(question.split()) if question else 0,
        "is_decomposed": len(sub_questions) > 1,
        "sub_questions": sub_questions
    }

