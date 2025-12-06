"""
Iterative search agent for multi-step codebase exploration.
Uses decomposed sub-questions to search iteratively and build up knowledge.
"""
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import json

from backend.modules.vector_store import FaissStore
from backend.modules.search import ripgrep_candidates, fuse_results
from backend.modules.question_decomposer import decompose_question
from backend.modules.context_retriever import expand_code_context
from backend.modules.reasoning_chain import ReasoningChain, extract_insights_with_llm
from backend.modules.answer_synthesis import synthesize_answer, synthesize_with_plan
from backend.config import DATA_DIR, TOP_K_EMB, TOP_K_RG, TOP_K_FINAL


class SearchStep:
    """Represents a single search step in the iterative process."""
    
    def __init__(self, query: str, step_number: int):
        self.query = query
        self.step_number = step_number
        self.results: List[Dict] = []
        self.files_found: Set[str] = set()
        self.key_concepts: Set[str] = set()
        self.completed = False
    
    def add_results(self, results: List[Dict]):
        """Add search results to this step."""
        self.results.extend(results)
        for result in results:
            file_path = result.get("file", "")
            if file_path:
                self.files_found.add(file_path)
        self.completed = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "query": self.query,
            "results_count": len(self.results),
            "files_found": list(self.files_found),
            "completed": self.completed
        }


class IterativeSearchAgent:
    """
    Agent that performs iterative searches to explore a codebase.
    Uses sub-questions to guide the search process.
    """
    
    def __init__(self, repo_dir: str, repo_id: str = None, base_dir: str = None, original_question: str = None):
        """
        Initialize the iterative search agent.
        
        Args:
            repo_dir: Repository directory to search
            repo_id: Repository ID (if None, will be generated from path)
            base_dir: Base directory for indices
            original_question: Original question being explored (for reasoning chain)
        """
        self.repo_dir = Path(repo_dir).resolve()
        if repo_id is None:
            from backend.modules.multi_repo import repo_id_from_path
            self.repo_id = repo_id_from_path(str(self.repo_dir))
        else:
            self.repo_id = repo_id
        
        if base_dir is None:
            base_dir = f"{DATA_DIR}/index"
        self.base_dir = base_dir
        
        # Load vector store
        self.store = FaissStore(self.repo_id, base_dir=base_dir)
        if not self.store.index_path.exists():
            raise ValueError(f"Repository not indexed: {self.repo_id}")
        self.store.load()
        
        # Track search steps
        self.search_steps: List[SearchStep] = []
        self.all_results: List[Dict] = []
        self.all_files: Set[str] = set()
        self.known_concepts: Set[str] = set()
        
        # Reasoning chain for tracking knowledge
        self.reasoning_chain: Optional[ReasoningChain] = None
        self._original_question = original_question or ""
    
    def search_single_query(self, query: str, top_k: int = TOP_K_FINAL, expand_context: bool = True) -> List[Dict]:
        """
        Perform a single search query.
        
        Args:
            query: Search query
            top_k: Maximum number of results
            expand_context: Whether to expand code context
        
        Returns:
            List of search results with repo_id added
        """
        # Hybrid search: ripgrep + vector
        rg_results = ripgrep_candidates(query, str(self.repo_dir), top_k=TOP_K_RG)
        vec_results = self.store.query(query, k=TOP_K_EMB)
        fused = fuse_results(rg_results, vec_results, top_k=top_k)
        
        # Add repo_id for consistency
        for result in fused:
            result["repo_id"] = self.repo_id
            result["repo_dir"] = str(self.repo_dir)
            result["search_query"] = query  # Track which query found this
        
        # Expand context if requested
        if expand_context:
            fused = expand_code_context(fused, str(self.repo_dir), context_lines=10)
        
        return fused
    
    def search_iterative(
        self,
        sub_questions: List[str],
        max_steps: int = None,
        results_per_step: int = TOP_K_FINAL,
        deduplicate: bool = True,
        use_reasoning_chain: bool = True
    ) -> Tuple[List[Dict], List[SearchStep], Optional[ReasoningChain]]:
        """
        Perform iterative searches for each sub-question.
        
        Args:
            sub_questions: List of sub-questions to search for
            max_steps: Maximum number of search steps (None = all)
            results_per_step: Maximum results per search step
            deduplicate: Whether to deduplicate results across steps
        
        Returns:
            Tuple of (all_results, search_steps)
        """
        if max_steps is None:
            max_steps = len(sub_questions)
        else:
            max_steps = min(max_steps, len(sub_questions))
        
        all_results = []
        search_steps = []
        seen_results = set()  # For deduplication: (file, start, end)
        
        # Initialize reasoning chain if requested
        if use_reasoning_chain:
            original_q = self._original_question if hasattr(self, '_original_question') else ""
            self.reasoning_chain = ReasoningChain(original_question=original_q or sub_questions[0] if sub_questions else "")
            print(f"[iterative_agent] Reasoning chain tracking enabled")
        
        print(f"[iterative_agent] Starting iterative search with {max_steps} steps")
        
        for i, query in enumerate(sub_questions[:max_steps], 1):
            print(f"[iterative_agent] Step {i}/{max_steps}: Searching for '{query[:60]}...'")
            
            step = SearchStep(query, i)
            
            # Get context from previous steps for informed searching
            previous_context = None
            if use_reasoning_chain and self.reasoning_chain and i > 1:
                previous_context = self.reasoning_chain.get_context_for_next_search(max_knowledge_entries=2)
                print(f"[iterative_agent] Using context from previous steps to inform search")
            
            # Perform search
            try:
                results = self.search_single_query(query, top_k=results_per_step, expand_context=True)
                
                # Deduplicate if requested
                if deduplicate:
                    unique_results = []
                    for result in results:
                        # Create unique key from file path and line range
                        file_path = result.get("file", "")
                        start = result.get("start", 0)
                        end = result.get("end", 0)
                        result_key = (file_path, start, end)
                        
                        if result_key not in seen_results:
                            seen_results.add(result_key)
                            unique_results.append(result)
                    results = unique_results
                
                step.add_results(results)
                all_results.extend(results)
                
                # Update tracking
                for result in results:
                    file_path = result.get("file", "")
                    if file_path:
                        self.all_files.add(file_path)
                
                # Add knowledge to reasoning chain
                if use_reasoning_chain and self.reasoning_chain:
                    insights = extract_insights_with_llm(query, results, previous_context)
                    self.reasoning_chain.add_knowledge(
                        step_number=i,
                        query=query,
                        search_results=results,
                        findings_summary=insights
                    )
                    print(f"[iterative_agent] Added knowledge to reasoning chain")
            
            except Exception as e:
                print(f"[iterative_agent] Error in step {i}: {e}")
                step.completed = False
            
            search_steps.append(step)
            print(f"[iterative_agent] Step {i} completed: {len(step.results)} results")
        
        self.search_steps = search_steps
        self.all_results = all_results
        
        print(f"[iterative_agent] Iterative search completed: {len(all_results)} total results from {len(search_steps)} steps")
        
        return all_results, search_steps, self.reasoning_chain
    
    def get_summary(self) -> Dict:
        """Get summary of the iterative search process."""
        summary = {
            "total_steps": len(self.search_steps),
            "completed_steps": sum(1 for step in self.search_steps if step.completed),
            "total_results": len(self.all_results),
            "unique_files": len(self.all_files),
            "steps": [step.to_dict() for step in self.search_steps]
        }
        
        # Add reasoning chain summary if available
        if self.reasoning_chain:
            summary["reasoning_chain"] = self.reasoning_chain.to_dict()
            summary["key_concepts"] = list(self.reasoning_chain.all_key_concepts)
            summary["discovered_files"] = list(self.reasoning_chain.discovered_files)
            summary["discovered_functions"] = list(self.reasoning_chain.discovered_functions)
            summary["discovered_classes"] = list(self.reasoning_chain.discovered_classes)
        
        return summary


def search_iterative_agent(
    repo_dir: str,
    question: str,
    decompose: bool = True,
    max_steps: int = None,
    results_per_step: int = TOP_K_FINAL,
    repo_id: str = None,
    base_dir: str = None
) -> Dict:
    """
    High-level function to perform iterative search with question decomposition.
    
    Args:
        repo_dir: Repository directory to search
        question: Original complex question
        decompose: Whether to decompose the question first
        max_steps: Maximum number of search steps
        results_per_step: Results per search step
        repo_id: Repository ID (optional)
        base_dir: Base directory for indices (optional)
    
    Returns:
        Dict with results, steps, and summary
    """
    # Decompose question if requested
    if decompose:
        print(f"[iterative_agent] Decomposing question: {question[:80]}...")
        sub_questions = decompose_question(question)
        print(f"[iterative_agent] Decomposed into {len(sub_questions)} sub-questions")
    else:
        # Use question as single sub-question
        sub_questions = [question]
    
    # Initialize agent with original question for reasoning chain
    agent = IterativeSearchAgent(repo_dir, repo_id=repo_id, base_dir=base_dir, original_question=question)
    
    # Perform iterative search with reasoning chain
    all_results, search_steps, reasoning_chain = agent.search_iterative(
        sub_questions,
        max_steps=max_steps,
        results_per_step=results_per_step,
        deduplicate=True,
        use_reasoning_chain=True
    )
    
    # Get summary (includes reasoning chain data)
    summary = agent.get_summary()
    
    # Generate reasoning summary
    reasoning_summary = None
    reasoning_chain_dict = None
    if reasoning_chain:
        reasoning_summary = reasoning_chain.generate_reasoning_summary()
        reasoning_chain_dict = reasoning_chain.to_dict()
    
    # Synthesize comprehensive answer from reasoning chain and results
    synthesized_answer_data = None
    if reasoning_chain and all_results:
        try:
            print(f"[iterative_agent] Synthesizing comprehensive answer...")
            synthesized_answer_data = synthesize_answer(
                question=question,
                reasoning_chain=reasoning_chain,
                search_results=all_results,
                temperature=0.3
            )
            print(f"[iterative_agent] Answer synthesis completed")
        except Exception as e:
            print(f"[iterative_agent] Answer synthesis failed: {e}")
            synthesized_answer_data = None
    
    return {
        "ok": True,
        "original_question": question,
        "sub_questions": sub_questions,
        "results": all_results,
        "search_steps": [step.to_dict() for step in search_steps],
        "summary": summary,
        "reasoning_chain": reasoning_chain_dict,
        "reasoning_summary": reasoning_summary,
        "synthesized_answer": synthesized_answer_data,
        "total_results": len(all_results),
        "unique_files": len(agent.all_files)
    }

