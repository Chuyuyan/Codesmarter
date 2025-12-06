"""
Answer synthesis for multi-step reasoning.
Combines findings from iterative search and reasoning chain into comprehensive answers.
"""
from typing import List, Dict, Optional, Any
from backend.modules.reasoning_chain import ReasoningChain
from backend.modules.llm_api import answer_with_citations, get_fresh_client
from backend.config import LLM_PROVIDER, LLM_MODEL, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY
import os


SYNTHESIS_PROMPT = """You are an expert code assistant analyzing a codebase through multi-step exploration. Based on the iterative search process and reasoning chain, synthesize a comprehensive answer to the user's question.

Instructions:
1. Review the reasoning chain to understand the exploration path
2. Synthesize findings from all search steps into a cohesive answer
3. Connect findings across different steps to provide a complete picture
4. Reference specific code locations using format: `filename:start-end`
5. Do NOT make up files, functions, or code that doesn't exist
6. If information is missing, clearly state what was not found
7. Structure your answer logically, building on what was discovered at each step

Original Question: {question}

Reasoning Chain Summary:
{reasoning_summary}

Code Evidence from All Steps:
{code_evidence}

Key Concepts Discovered:
{key_concepts}

Files Analyzed: {files_count}
Functions Identified: {functions_count}
Classes Identified: {classes_count}

Provide a comprehensive answer that synthesizes all the findings from the multi-step exploration.
"""


def synthesize_answer(
    question: str,
    reasoning_chain: ReasoningChain,
    search_results: List[Dict],
    model: Optional[str] = None,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Synthesize a comprehensive answer from reasoning chain and search results.
    
    Args:
        question: Original question
        reasoning_chain: Reasoning chain with knowledge from all steps
        search_results: All search results from iterative exploration
        model: Optional model override
        temperature: Temperature for LLM generation
    
    Returns:
        Dictionary with synthesized answer and metadata
    """
    # Generate reasoning summary
    reasoning_summary = reasoning_chain.generate_reasoning_summary()
    
    # Prepare code evidence (limit to avoid token limits)
    max_results = min(len(search_results), 15)  # Limit to top 15 results
    code_evidence_parts = []
    seen_files = set()
    
    for result in search_results[:max_results]:
        file_path = result.get("file", "")
        start = result.get("start", 0)
        end = result.get("end", 0)
        snippet = result.get("snippet", "")
        
        # Show file name only once, then just snippets
        if file_path not in seen_files:
            code_evidence_parts.append(f"\n--- File: {file_path} ---")
            seen_files.add(file_path)
        
        code_evidence_parts.append(f"[{file_path}:{start}-{end}]\n```\n{snippet}\n```\n")
    
    code_evidence = "\n".join(code_evidence_parts)
    
    # Prepare key concepts
    key_concepts = ", ".join(list(reasoning_chain.all_key_concepts)[:20])  # Top 20 concepts
    
    # Build synthesis prompt
    prompt = SYNTHESIS_PROMPT.format(
        question=question,
        reasoning_summary=reasoning_summary,
        code_evidence=code_evidence,
        key_concepts=key_concepts,
        files_count=len(reasoning_chain.discovered_files),
        functions_count=len(reasoning_chain.discovered_functions),
        classes_count=len(reasoning_chain.discovered_classes)
    )
    
    # Generate synthesized answer using LLM
    try:
        # Model selection
        if model:
            model_to_use = model
        elif os.getenv("LLM_MODEL"):
            model_to_use = os.getenv("LLM_MODEL")
        elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY and os.getenv("OPENAI_MODEL"):
            model_to_use = os.getenv("OPENAI_MODEL")
        else:
            model_to_use = LLM_MODEL
        
        # Handle Anthropic separately
        if LLM_PROVIDER == "anthropic":
            try:
                from anthropic import Anthropic
                anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                message = anthropic_client.messages.create(
                    model=model_to_use,
                    max_tokens=4096,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                synthesized_answer = message.content[0].text
            except Exception as e:
                raise Exception(f"Anthropic API error: {str(e)}")
        else:
            # OpenAI-compatible providers
            api_client = get_fresh_client()
            rsp = api_client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                timeout=180  # Longer timeout for synthesis
            )
            synthesized_answer = rsp.choices[0].message.content
        
        return {
            "synthesized_answer": synthesized_answer,
            "reasoning_summary": reasoning_summary,
            "key_concepts": list(reasoning_chain.all_key_concepts),
            "files_analyzed": len(reasoning_chain.discovered_files),
            "functions_identified": len(reasoning_chain.discovered_functions),
            "classes_identified": len(reasoning_chain.discovered_classes),
            "search_steps_completed": reasoning_chain.completed_steps,
            "code_snippets_used": min(len(search_results), max_results)
        }
    
    except Exception as e:
        # Fallback: use regular answer_with_citations if synthesis fails
        print(f"[answer_synthesis] Synthesis failed: {e}, falling back to regular answer")
        fallback_answer = answer_with_citations(question, search_results[:10], temperature=temperature)
        return {
            "synthesized_answer": fallback_answer,
            "reasoning_summary": reasoning_summary,
            "key_concepts": list(reasoning_chain.all_key_concepts),
            "files_analyzed": len(reasoning_chain.discovered_files),
            "functions_identified": len(reasoning_chain.discovered_functions),
            "classes_identified": len(reasoning_chain.discovered_classes),
            "search_steps_completed": reasoning_chain.completed_steps,
            "code_snippets_used": min(len(search_results), 10),
            "synthesis_error": str(e)
        }


def synthesize_with_plan(
    question: str,
    reasoning_chain: ReasoningChain,
    search_results: List[Dict],
    plan: Optional[List[str]] = None,
    model: Optional[str] = None,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Synthesize answer with explicit plan execution.
    
    Args:
        question: Original question
        reasoning_chain: Reasoning chain with knowledge
        search_results: All search results
        plan: Optional explicit plan (list of steps/tasks)
        model: Optional model override
        temperature: Temperature for LLM generation
    
    Returns:
        Dictionary with synthesized answer and plan execution details
    """
    # If no plan provided, use knowledge entries as plan steps
    if plan is None:
        plan = [entry.query for entry in reasoning_chain.knowledge_entries]
    
    # Synthesize answer
    synthesis_result = synthesize_answer(
        question,
        reasoning_chain,
        search_results,
        model=model,
        temperature=temperature
    )
    
    # Add plan execution details
    synthesis_result["plan"] = plan
    synthesis_result["plan_steps_completed"] = len(reasoning_chain.knowledge_entries)
    synthesis_result["plan_steps_total"] = len(plan)
    
    return synthesis_result

