"""
Reasoning chain and context tracking for iterative codebase exploration.
Tracks what we learn from each search step and builds up knowledge incrementally.
"""
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
import json


class KnowledgeEntry:
    """Represents a piece of knowledge learned from a search step."""
    
    def __init__(self, step_number: int, query: str, findings: str, key_concepts: List[str] = None):
        """
        Initialize a knowledge entry.
        
        Args:
            step_number: Which search step this came from
            query: The search query that led to this knowledge
            findings: Summary of what was learned
            key_concepts: List of key concepts/terms discovered
        """
        self.step_number = step_number
        self.query = query
        self.findings = findings
        self.key_concepts = key_concepts or []
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "query": self.query,
            "findings": self.findings,
            "key_concepts": self.key_concepts,
            "timestamp": self.timestamp
        }


class ReasoningChain:
    """
    Tracks the reasoning chain and knowledge discovered during iterative search.
    Builds up context incrementally as we explore the codebase.
    """
    
    def __init__(self, original_question: str):
        """
        Initialize the reasoning chain.
        
        Args:
            original_question: The original complex question being explored
        """
        self.original_question = original_question
        self.knowledge_entries: List[KnowledgeEntry] = []
        self.all_key_concepts: Set[str] = set()
        self.discovered_files: Set[str] = set()
        self.discovered_functions: Set[str] = set()
        self.discovered_classes: Set[str] = set()
        self.reasoning_summary: str = ""
        self.completed_steps: int = 0
    
    def add_knowledge(
        self,
        step_number: int,
        query: str,
        search_results: List[Dict],
        findings_summary: Optional[str] = None
    ):
        """
        Add knowledge from a search step.
        
        Args:
            step_number: Step number in the iterative search
            query: Search query used
            search_results: List of search results from this step
            findings_summary: Optional LLM-generated summary of findings
        """
        # Extract key information from results
        key_concepts = self._extract_key_concepts(search_results, query)
        files = [r.get("file", "") for r in search_results if r.get("file")]
        
        # If no summary provided, create a simple one
        if findings_summary is None:
            findings_summary = self._create_findings_summary(query, search_results, key_concepts)
        
        # Create knowledge entry
        entry = KnowledgeEntry(
            step_number=step_number,
            query=query,
            findings=findings_summary,
            key_concepts=key_concepts
        )
        
        self.knowledge_entries.append(entry)
        
        # Update tracking sets
        self.all_key_concepts.update(key_concepts)
        self.discovered_files.update(files)
        
        # Extract functions and classes from snippets
        for result in search_results:
            snippet = result.get("snippet", "")
            self._extract_functions_and_classes(snippet)
        
        self.completed_steps += 1
    
    def _extract_key_concepts(self, results: List[Dict], query: str) -> List[str]:
        """
        Extract key concepts from search results.
        
        Args:
            results: Search results
            query: Original query
        
        Returns:
            List of key concepts discovered
        """
        concepts = set()
        
        # Add words from query (likely important)
        query_words = query.lower().split()
        important_words = ["authentication", "auth", "login", "token", "session", "function", "component", 
                          "api", "endpoint", "route", "handler", "module", "class", "method"]
        
        for word in query_words:
            if len(word) > 3 and word not in ["the", "and", "are", "how", "what", "where", "when", "why"]:
                concepts.add(word)
        
        # Extract from file names
        for result in results:
            file_path = result.get("file", "")
            if file_path:
                file_name = file_path.split("\\")[-1].split("/")[-1]
                # Remove extension
                base_name = file_name.split(".")[0]
                if base_name and len(base_name) > 2:
                    concepts.add(base_name.lower())
        
        # Extract from snippets (look for common patterns)
        for result in results:
            snippet = result.get("snippet", "").lower()
            
            # Look for function definitions
            if "def " in snippet or "function " in snippet or "const " in snippet:
                # Try to extract function/class names
                lines = snippet.split("\n")
                for line in lines[:5]:  # Check first few lines
                    if "def " in line:
                        parts = line.split("def ")
                        if len(parts) > 1:
                            func_name = parts[1].split("(")[0].strip()
                            if func_name:
                                concepts.add(func_name)
                    elif "class " in line:
                        parts = line.split("class ")
                        if len(parts) > 1:
                            class_name = parts[1].split(":")[0].split("(")[0].strip()
                            if class_name:
                                concepts.add(class_name)
        
        return list(concepts)[:15]  # Limit to top 15 concepts
    
    def _extract_functions_and_classes(self, snippet: str):
        """Extract function and class names from code snippet."""
        lines = snippet.split("\n")
        for line in lines[:20]:  # Check first 20 lines
            line_stripped = line.strip()
            
            # Python functions
            if line_stripped.startswith("def "):
                func_name = line_stripped.split("def ")[1].split("(")[0].strip()
                if func_name:
                    self.discovered_functions.add(func_name)
            
            # Python classes
            elif line_stripped.startswith("class "):
                class_name = line_stripped.split("class ")[1].split(":")[0].split("(")[0].strip()
                if class_name:
                    self.discovered_classes.add(class_name)
            
            # JavaScript/TypeScript functions
            elif "function " in line_stripped:
                parts = line_stripped.split("function ")
                if len(parts) > 1:
                    func_name = parts[1].split("(")[0].strip()
                    if func_name:
                        self.discovered_functions.add(func_name)
            
            # JavaScript/TypeScript classes
            elif "class " in line_stripped and not line_stripped.startswith("#"):
                parts = line_stripped.split("class ")
                if len(parts) > 1:
                    class_name = parts[1].split("{")[0].split("(")[0].strip()
                    if class_name:
                        self.discovered_classes.add(class_name)
    
    def _create_findings_summary(self, query: str, results: List[Dict], key_concepts: List[str]) -> str:
        """
        Create a simple summary of findings from search results.
        
        Args:
            query: Search query
            results: Search results
            key_concepts: Key concepts discovered
        
        Returns:
            Summary string
        """
        if not results:
            return f"No results found for query: {query}"
        
        files_found = list(set([r.get("file", "") for r in results if r.get("file")]))[:5]
        files_summary = ", ".join([f.split("\\")[-1].split("/")[-1] for f in files_found[:3]])
        
        summary_parts = [
            f"Found {len(results)} result(s) for query: '{query}'"
        ]
        
        if files_summary:
            summary_parts.append(f"Relevant files: {files_summary}")
        
        if key_concepts:
            summary_parts.append(f"Key concepts: {', '.join(key_concepts[:5])}")
        
        return ". ".join(summary_parts) + "."
    
    def generate_reasoning_summary(self) -> str:
        """
        Generate a summary of the reasoning chain.
        
        Returns:
            Summary of what we've learned across all steps
        """
        if not self.knowledge_entries:
            return "No knowledge accumulated yet."
        
        summary_parts = [
            f"Reasoning chain for question: '{self.original_question}'",
            f"Completed {self.completed_steps} search steps.",
            "",
            "Knowledge discovered:"
        ]
        
        for entry in self.knowledge_entries:
            summary_parts.append(f"\nStep {entry.step_number}: {entry.query}")
            summary_parts.append(f"  → {entry.findings}")
            if entry.key_concepts:
                summary_parts.append(f"  Key concepts: {', '.join(entry.key_concepts[:5])}")
        
        summary_parts.append(f"\nSummary:")
        summary_parts.append(f"  - {len(self.discovered_files)} unique files discovered")
        summary_parts.append(f"  - {len(self.discovered_functions)} functions identified")
        summary_parts.append(f"  - {len(self.discovered_classes)} classes identified")
        summary_parts.append(f"  - {len(self.all_key_concepts)} key concepts tracked")
        
        self.reasoning_summary = "\n".join(summary_parts)
        return self.reasoning_summary
    
    def get_context_for_next_search(self, max_knowledge_entries: int = 3) -> str:
        """
        Get context summary for informing the next search.
        
        Args:
            max_knowledge_entries: Maximum number of recent knowledge entries to include
        
        Returns:
            Context string to inform next search
        """
        if not self.knowledge_entries:
            return ""
        
        context_parts = [
            "Previous findings:"
        ]
        
        # Include recent knowledge entries
        recent_entries = self.knowledge_entries[-max_knowledge_entries:]
        for entry in recent_entries:
            context_parts.append(f"- {entry.findings}")
        
        # Include key concepts
        if self.all_key_concepts:
            context_parts.append(f"\nKey concepts discovered: {', '.join(list(self.all_key_concepts)[:10])}")
        
        # Include discovered files
        if self.discovered_files:
            file_names = [f.split("\\")[-1].split("/")[-1] for f in list(self.discovered_files)[:5]]
            context_parts.append(f"\nRelevant files found: {', '.join(file_names)}")
        
        return "\n".join(context_parts)
    
    def to_dict(self) -> Dict:
        """Convert reasoning chain to dictionary for serialization."""
        return {
            "original_question": self.original_question,
            "completed_steps": self.completed_steps,
            "knowledge_entries": [entry.to_dict() for entry in self.knowledge_entries],
            "all_key_concepts": list(self.all_key_concepts),
            "discovered_files": list(self.discovered_files),
            "discovered_functions": list(self.discovered_functions),
            "discovered_classes": list(self.discovered_classes),
            "reasoning_summary": self.reasoning_summary or self.generate_reasoning_summary()
        }


def extract_insights_with_llm(
    query: str,
    search_results: List[Dict],
    previous_context: Optional[str] = None
) -> str:
    """
    Use LLM to extract key insights from search results.
    
    Args:
        query: The search query
        search_results: List of search results
        previous_context: Previous knowledge from earlier steps (optional)
    
    Returns:
        LLM-generated summary of insights
    """
    # For now, return a simple summary
    # In the future, could use LLM to generate more sophisticated insights
    if not search_results:
        return f"No relevant code found for query: '{query}'"
    
    files_found = list(set([r.get("file", "") for r in search_results if r.get("file")]))
    file_names = [f.split("\\")[-1].split("/")[-1] for f in files_found[:5]]
    
    summary = f"Found {len(search_results)} relevant code snippet(s) in {len(files_found)} file(s): {', '.join(file_names)}"
    
    if previous_context:
        summary = f"{previous_context}\n\n{summary}"
    
    return summary

