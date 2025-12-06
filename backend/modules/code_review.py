"""
Code Review Module
Analyzes code for bugs, security vulnerabilities, performance issues, and code quality.
"""
from typing import List, Dict, Optional, Any
from backend.modules.llm_api import get_client
from backend.config import LLM_MODEL


REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following code and identify:
1. **Bugs**: Logic errors, potential runtime exceptions, edge cases not handled
2. **Security Issues**: SQL injection, XSS, authentication flaws, sensitive data exposure, insecure configurations
3. **Performance Issues**: Inefficient algorithms, N+1 queries, memory leaks, blocking operations
4. **Code Quality**: Code smells, best practices violations, maintainability issues
5. **Improvements**: Suggestions for better code structure, readability, and maintainability

Code to review:
```{language}
{code}
```

{context}

Review Type: {review_type}

Provide a comprehensive review report in the following format:

## 🐛 Bugs Found
- [Bug description] (Severity: High/Medium/Low)
  - Location: [file:line]
  - Issue: [detailed explanation]
  - Fix: [suggested fix]

## 🔒 Security Issues
- [Security issue description] (Severity: Critical/High/Medium)
  - Location: [file:line]
  - Vulnerability: [detailed explanation]
  - Risk: [what could happen]
  - Fix: [suggested fix]

## ⚡ Performance Issues
- [Performance issue description] (Severity: High/Medium/Low)
  - Location: [file:line]
  - Impact: [performance impact]
  - Fix: [suggested optimization]

## 📋 Code Quality Issues
- [Quality issue description] (Severity: Medium/Low)
  - Location: [file:line]
  - Issue: [detailed explanation]
  - Fix: [suggested improvement]

## ✅ Positive Observations
- [What's good about the code]

## 📊 Summary
- Total Issues: [count]
- Critical/High: [count]
- Medium: [count]
- Low: [count]
- Overall Code Quality: [Excellent/Good/Fair/Needs Improvement]
"""


def review_code(
    code: str,
    language: str = "python",
    file_path: Optional[str] = None,
    repo_dir: Optional[str] = None,
    review_type: str = "comprehensive",
    code_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Review code for bugs, security issues, performance problems, and code quality.
    
    Args:
        code: The code to review
        language: Programming language (python, javascript, typescript, etc.)
        file_path: Path to the file being reviewed
        repo_dir: Root directory of the repository (for context)
        review_type: Type of review (comprehensive, security, performance, quality, bugs)
        code_context: Additional context about the code (e.g., related files, imports)
    
    Returns:
        Dictionary with review results including:
        - review_report: Markdown-formatted review report
        - bugs: List of bugs found
        - security_issues: List of security issues
        - performance_issues: List of performance issues
        - quality_issues: List of code quality issues
        - summary: Summary statistics
    """
    try:
        client = get_client()
        
        # Build context section if available
        context_section = ""
        if code_context:
            context_section = f"\nAdditional Context:\n{code_context}\n"
        elif file_path and repo_dir:
            context_section = f"\nFile: {file_path}\nRepository: {repo_dir}\n"
        
        # Build prompt
        prompt = REVIEW_PROMPT.format(
            language=language,
            code=code,
            context=context_section,
            review_type=review_type
        )
        
        # Call LLM
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert code reviewer with deep knowledge of software security, performance optimization, and code quality best practices."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent, focused reviews
            max_tokens=4000
        )
        
        review_report = response.choices[0].message.content
        
        # Parse the review report to extract structured data
        parsed_results = parse_review_report(review_report, file_path)
        
        return {
            "ok": True,
            "review_report": review_report,
            "review_type": review_type,
            "language": language,
            "file_path": file_path,
            **parsed_results
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "review_report": None
        }


def parse_review_report(review_report: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse the review report to extract structured information.
    
    Args:
        review_report: The markdown-formatted review report
        file_path: Path to the file being reviewed
    
    Returns:
        Dictionary with parsed review data
    """
    bugs = []
    security_issues = []
    performance_issues = []
    quality_issues = []
    
    lines = review_report.split('\n')
    current_section = None
    current_item = {}
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('## 🐛 Bugs Found'):
            current_section = 'bugs'
        elif line.startswith('## 🔒 Security Issues'):
            current_section = 'security'
        elif line.startswith('## ⚡ Performance Issues'):
            current_section = 'performance'
        elif line.startswith('## 📋 Code Quality Issues'):
            current_section = 'quality'
        elif line.startswith('- ['):
            # Start of a new item
            if current_item:
                # Save previous item
                if current_section == 'bugs':
                    bugs.append(current_item)
                elif current_section == 'security':
                    security_issues.append(current_item)
                elif current_section == 'performance':
                    performance_issues.append(current_item)
                elif current_section == 'quality':
                    quality_issues.append(current_item)
            
            # Parse item title
            title_match = line[3:].split(']', 1)
            if len(title_match) == 2:
                title = title_match[0].strip()
                current_item = {
                    'title': title,
                    'severity': extract_severity(title_match[1]) if len(title_match) > 1 else 'Medium',
                    'description': '',
                    'location': file_path or 'Unknown',
                    'fix': ''
                }
        elif line.startswith('  - Location:'):
            current_item['location'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif line.startswith('  - Issue:') or line.startswith('  - Vulnerability:') or line.startswith('  - Impact:'):
            current_item['description'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif line.startswith('  - Fix:'):
            current_item['fix'] = line.split(':', 1)[1].strip() if ':' in line else ''
    
    # Add last item
    if current_item:
        if current_section == 'bugs':
            bugs.append(current_item)
        elif current_section == 'security':
            security_issues.append(current_item)
        elif current_section == 'performance':
            performance_issues.append(current_item)
        elif current_section == 'quality':
            quality_issues.append(current_item)
    
    # Extract summary
    summary = extract_summary(review_report)
    
    return {
        "bugs": bugs,
        "security_issues": security_issues,
        "performance_issues": performance_issues,
        "quality_issues": quality_issues,
        "summary": summary
    }


def extract_severity(text: str) -> str:
    """Extract severity from text."""
    text_lower = text.lower()
    if 'critical' in text_lower:
        return 'Critical'
    elif 'high' in text_lower:
        return 'High'
    elif 'medium' in text_lower:
        return 'Medium'
    elif 'low' in text_lower:
        return 'Low'
    return 'Medium'


def extract_summary(review_report: str) -> Dict[str, Any]:
    """Extract summary statistics from review report."""
    summary = {
        "total_issues": 0,
        "critical_high": 0,
        "medium": 0,
        "low": 0,
        "overall_quality": "Unknown"
    }
    
    lines = review_report.split('\n')
    for line in lines:
        if 'Total Issues:' in line:
            try:
                count = int(line.split(':')[1].strip().split()[0])
                summary["total_issues"] = count
            except:
                pass
        elif 'Critical/High:' in line or 'Critical/High:' in line:
            try:
                count = int(line.split(':')[1].strip().split()[0])
                summary["critical_high"] = count
            except:
                pass
        elif 'Medium:' in line and 'Total' not in line:
            try:
                count = int(line.split(':')[1].strip().split()[0])
                summary["medium"] = count
            except:
                pass
        elif 'Low:' in line:
            try:
                count = int(line.split(':')[1].strip().split()[0])
                summary["low"] = count
            except:
                pass
        elif 'Overall Code Quality:' in line:
            quality = line.split(':')[1].strip()
            summary["overall_quality"] = quality
    
    return summary


def stream_review_code(
    code: str,
    language: str = "python",
    file_path: Optional[str] = None,
    repo_dir: Optional[str] = None,
    review_type: str = "comprehensive",
    code_context: Optional[str] = None
):
    """
    Stream code review results as they are generated.
    
    Yields:
        SSE-formatted chunks with review report
    """
    import json
    
    try:
        client = get_client()
        
        # Build context section
        context_section = ""
        if code_context:
            context_section = f"\nAdditional Context:\n{code_context}\n"
        elif file_path and repo_dir:
            context_section = f"\nFile: {file_path}\nRepository: {repo_dir}\n"
        
        # Build prompt
        prompt = REVIEW_PROMPT.format(
            language=language,
            code=code,
            context=context_section,
            review_type=review_type
        )
        
        # Send start event
        yield f"data: {json.dumps({'type': 'start', 'message': 'Starting code review...'})}\n\n"
        
        # Stream response
        full_content = ""
        stream = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert code reviewer with deep knowledge of software security, performance optimization, and code quality best practices."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
        
        # Parse results
        parsed_results = parse_review_report(full_content, file_path)
        
        # Send done event with metadata
        yield f"data: {json.dumps({'type': 'done', 'review_type': review_type, 'language': language, 'file_path': file_path, **parsed_results})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

