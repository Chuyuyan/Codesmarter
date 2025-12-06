"""
Automatic analysis type detection from user questions.
Detects whether user wants to: explain, refactor, debug, or optimize.
"""
import re
from typing import Dict, Optional


# Keyword patterns for each analysis type
# Expanded with more synonyms, phrases, and variations
ANALYSIS_KEYWORDS = {
    "generate": [
        # Direct requests (English)
        r"build\s+me", r"create\s+a", r"generate\s+a", r"make\s+me\s+a",
        r"build\s+a", r"create\s+me\s+a", r"generate\s+me\s+a",
        r"i\s+want\s+to\s+build", r"i\s+want\s+to\s+create",
        r"can\s+you\s+build", r"can\s+you\s+create", r"can\s+you\s+generate",
        # Project-related (English)
        r"full\s+stack", r"fullstack", r"full\s+project",
        r"complete\s+app", r"complete\s+application", r"entire\s+project",
        r"web\s+app", r"web\s+application", r"website",
        # Stack mentions (indicates generation) (English)
        r"with\s+react\s+and\s+flask", r"react\s+frontend\s+and\s+backend",
        r"frontend\s+and\s+backend", r"frontend\s+backend\s+database",
        r"with\s+database", r"connect\s+to\s+database",
        # Chinese keywords
        r"创建", r"生成", r"构建", r"建立", r"做一个", r"帮我做",
        r"新建", r"搭建", r"开发", r"写一个", r"做一个", r"生成一个",
        r"全栈", r"完整项目", r"整个应用", r"网站", r"应用",
        r"前端", r"后端", r"数据库", r"连接数据库",
        r"创建一个", r"生成一个", r"构建一个", r"新建项目", r"创建项目"
    ],
    "explain": [
        # Direct requests (English)
        r"how\s+does", r"what\s+does", r"explain", r"understand",
        r"how\s+it\s+works", r"what\s+is", r"tell\s+me\s+about",
        r"describe", r"walk\s+me\s+through", r"help\s+me\s+understand",
        r"can\s+you\s+explain", r"what's\s+this", r"how\s+this\s+works",
        r"what\s+is\s+this", r"how\s+does\s+this", r"what\s+does\s+this",
        r"meaning\s+of", r"purpose\s+of", r"what\s+is\s+the",
        # Additional variations (English)
        r"what\s+do\s+these", r"how\s+do\s+these", r"what\s+are\s+these",
        r"clarify", r"elaborate", r"break\s+down", r"show\s+me",
        r"teach\s+me", r"learn\s+about", r"documentation", r"guide",
        # Chinese keywords
        r"解释", r"说明", r"讲解", r"介绍", r"什么是", r"怎么", r"如何",
        r"为什么", r"什么意思", r"作用", r"功能", r"用途", r"含义",
        r"帮我理解", r"告诉我", r"描述", r"讲解一下", r"说明一下",
        r"这是什么", r"这是做什么", r"怎么工作", r"如何工作"
    ],
    "refactor": [
        # Direct requests (English)
        r"refactor", r"improve", r"clean\s+up", r"make\s+it\s+better",
        r"code\s+quality", r"maintainability", r"readability",
        r"restructure", r"reorganize", r"better\s+code",
        r"how\s+can\s+I\s+improve", r"make\s+this\s+cleaner",
        r"code\s+review", r"best\s+practices", r"clean\s+code",
        r"improve\s+this", r"make\s+better", r"code\s+quality",
        # Additional variations (English)
        r"refactoring", r"restructure", r"reorganize", r"polish",
        r"enhance", r"modernize", r"simplify", r"cleaner",
        r"better\s+structure", r"improve\s+design", r"code\s+style",
        r"follow\s+patterns", r"design\s+patterns", r"technical\s+debt",
        r"make\s+it\s+cleaner", r"code\s+organization",
        # Chinese keywords
        r"重构", r"改进", r"优化代码", r"改善", r"提升", r"改进代码",
        r"代码质量", r"可维护性", r"可读性", r"整理代码", r"清理代码",
        r"代码审查", r"最佳实践", r"代码风格", r"设计模式", r"技术债务",
        r"重构代码", r"优化结构", r"改进设计", r"简化代码"
    ],
    "debug": [
        # Direct issues (English)
        r"bug", r"error", r"issue", r"problem", r"not\s+working",
        r"broken", r"fix", r"wrong", r"fails", r"crash",
        r"exception", r"debug", r"what's\s+wrong", r"why\s+doesn't",
        r"why\s+isn't", r"doesn't\s+work", r"not\s+functioning",
        r"fix\s+this", r"what's\s+the\s+problem", r"why\s+is\s+this\s+broken",
        r"error\s+in", r"issue\s+with", r"problem\s+with", r"broken\s+code",
        # Additional variations (English)
        r"malfunction", r"defect", r"fault", r"glitch", r"failure",
        r"doesn't\s+function", r"not\s+functioning", r"malfunctioning",
        r"something's\s+wrong", r"something\s+wrong", r"not\s+right",
        r"incorrect", r"faulty", r"broken\s+down", r"not\s+operating",
        r"troubleshoot", r"diagnose", r"investigate", r"find\s+the\s+issue",
        r"what's\s+the\s+error", r"why\s+is\s+this\s+failing",
        r"unexpected\s+behavior", r"behaves\s+incorrectly", r"not\s+behaving",
        # Chinese keywords
        r"错误", r"问题", r"bug", r"故障", r"异常", r"报错", r"出错",
        r"修复", r"解决", r"调试", r"排错", r"不工作", r"不能用", r"不能用",
        r"出错了", r"有问题", r"出问题", r"为什么不行", r"为什么不能用",
        r"哪里错了", r"什么错误", r"怎么修复", r"如何修复", r"怎么解决",
        r"排查", r"诊断", r"检查", r"找出问题", r"定位问题"
    ],
    "optimize": [
        # Direct performance issues (English)
        r"slow", r"performance", r"optimize", r"faster",
        r"speed", r"bottleneck", r"efficient", r"optimization",
        r"make\s+it\s+faster", r"why\s+is\s+it\s+slow", r"improve\s+speed",
        r"performance\s+issue", r"too\s+slow", r"optimization",
        r"make\s+faster", r"speed\s+up", r"performance\s+problem",
        r"inefficient", r"bottleneck", r"optimize\s+this",
        # Additional variations (English)
        r"suboptimal", r"unacceptable\s+performance", r"execution\s+time",
        r"runtime", r"too\s+slow", r"very\s+slow", r"extremely\s+slow",
        r"performance\s+issue", r"performance\s+problem", r"performance\s+concern",
        r"slow\s+execution", r"slow\s+performance", r"lag", r"latency",
        r"response\s+time", r"throughput", r"scalability", r"efficiency",
        r"optimize\s+performance", r"improve\s+performance", r"boost\s+performance",
        r"make\s+it\s+run\s+faster", r"speed\s+optimization", r"performance\s+optimization",
        # Chinese keywords
        r"慢", r"性能", r"优化", r"加速", r"速度", r"瓶颈", r"效率",
        r"性能问题", r"太慢", r"很慢", r"优化性能", r"提升性能", r"提高速度",
        r"为什么慢", r"怎么优化", r"如何优化", r"性能优化", r"速度优化",
        r"执行时间", r"运行时间", r"响应时间", r"延迟", r"吞吐量", r"可扩展性",
        r"为什么这么慢", r"为什么很慢", r"太慢了", r"很慢了"
    ],
    "generate": [
        r"generate", r"create", r"build", r"make\s+me", r"make\s+a",
        r"i\s+want", r"i\s+need", r"build\s+a", r"create\s+a",
        r"new\s+project", r"full\s+stack", r"frontend\s+backend",
        r"todo\s+app", r"blog", r"e-commerce", r"web\s+app",
        r"generate\s+a", r"create\s+project", r"build\s+project",
        r"scaffold", r"initialize", r"set\s+up", r"new\s+app",
        r"full\s+stack\s+app", r"web\s+application", r"application"
    ]
}

# Strong keywords that are very reliable indicators
# If one of these is found, we can trust the keyword result even with score=1
STRONG_KEYWORDS = {
    "explain": ["explain", "how does", "what does", "understand", "describe",
                "解释", "说明", "讲解", "什么是", "怎么", "如何"],
    "refactor": ["refactor", "refactoring", "restructure", "reorganize",
                 "重构", "改进", "优化代码", "代码质量"],
    "debug": ["bug", "error", "broken", "fix", "debug", "crash", "exception",
              "错误", "问题", "修复", "调试", "报错", "异常"],
    "optimize": ["slow", "performance", "optimize", "faster", "speed", "bottleneck",
                 "慢", "性能", "优化", "加速", "速度", "瓶颈"],
    "generate": ["generate", "create", "build", "make me", "new project", "full stack",
                 "创建", "生成", "构建", "建立", "做一个", "新建"]
}


def detect_analysis_type_keywords(question: str) -> Dict[str, int]:
    """
    Detect analysis type using keyword matching.
    Returns scores for each type.
    
    Args:
        question: User's question
    
    Returns:
        Dictionary with scores for each analysis type
    """
    question_lower = question.lower()
    scores = {type_name: 0 for type_name in ANALYSIS_KEYWORDS.keys()}
    
    for analysis_type, patterns in ANALYSIS_KEYWORDS.items():
        for pattern in patterns:
            matches = len(re.findall(pattern, question_lower, re.IGNORECASE))
            scores[analysis_type] += matches
    
    return scores


def _has_strong_keyword(question: str, analysis_type: str) -> bool:
    """
    Check if question contains a strong keyword for the given analysis type.
    Strong keywords are very reliable indicators.
    """
    question_lower = question.lower()
    strong_keywords = STRONG_KEYWORDS.get(analysis_type, [])
    
    for keyword in strong_keywords:
        if keyword in question_lower:
            return True
    return False


def _llm_detect_analysis_type(question: str) -> Optional[str]:
    """
    Use LLM to detect analysis type.
    Returns detected type or None if LLM call fails.
    """
    try:
        from backend.modules.llm_api import get_fresh_client
        from backend.config import LLM_MODEL
        
        client = get_fresh_client()
        
        prompt = f"""Analyze this question (which may be in English or Chinese) and determine the best analysis type:
- "explain": User wants to understand how code works (解释/说明/讲解)
- "refactor": User wants to improve code quality/maintainability (重构/改进/优化代码)
- "debug": User wants to find bugs or fix issues (调试/修复/错误)
- "optimize": User wants to improve performance/speed (性能优化/加速)
- "generate": User wants to create/build/generate a new project or code (创建/生成/构建)

Question: {question}

Respond with ONLY one word: explain, refactor, debug, optimize, or generate"""
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        
        detected = response.choices[0].message.content.strip().lower()
        # Extract first valid word if response contains multiple words
        for word in detected.split():
            if word in ["explain", "refactor", "debug", "optimize", "generate"]:
                return word
        
        return None
    except Exception as e:
        print(f"[analysis_detector] LLM detection failed: {e}")
        return None


def detect_analysis_type(question: str, use_llm: bool = False) -> str:
    """
    Automatically detect analysis type from question.
    
    Uses a hybrid approach:
    1. Keyword-based detection first (fast, free)
    2. Checks for strong keywords (very reliable)
    3. Uses LLM for ambiguous cases if enabled (accurate but slower)
    
    Args:
        question: User's question
        use_llm: If True, use LLM for detection when confidence is low
    
    Returns:
        Analysis type: "explain", "refactor", "debug", or "optimize"
    """
    if not question or not question.strip():
        return "explain"  # Default for empty questions
    
    # Step 1: Keyword-based detection
    scores = detect_analysis_type_keywords(question)
    max_score = max(scores.values())
    best_type = max(scores, key=scores.get)
    
    # Step 2: High confidence (score >= 2) - use keyword result immediately
    if max_score >= 2:
        print(f"[analysis_detector] High confidence: {best_type} (score: {max_score})")
        return best_type
    
    # Step 3: Medium confidence (score = 1) - check for strong keywords
    if max_score == 1:
        # If strong keyword found, trust it (fast, accurate)
        if _has_strong_keyword(question, best_type):
            print(f"[analysis_detector] Medium confidence with strong keyword: {best_type}")
            return best_type
        
        # No strong keyword - use LLM if enabled for better accuracy
        if use_llm:
            print(f"[analysis_detector] Medium confidence, using LLM for accuracy...")
            llm_result = _llm_detect_analysis_type(question)
            if llm_result:
                print(f"[analysis_detector] LLM detected: {llm_result}")
                return llm_result
            # LLM failed, fall through to keyword result
        
        # Use keyword result (might be wrong, but fast)
        print(f"[analysis_detector] Medium confidence: {best_type} (score: {max_score})")
        return best_type
    
    # Step 4: No keywords found (score = 0) - definitely need help
    if max_score == 0:
        if use_llm:
            print(f"[analysis_detector] No keywords found, using LLM...")
            llm_result = _llm_detect_analysis_type(question)
            if llm_result:
                print(f"[analysis_detector] LLM detected: {llm_result}")
                return llm_result
        
        # No keywords and LLM not enabled or failed - default to explain
        print(f"[analysis_detector] No keywords found, defaulting to 'explain'")
        return "explain"
    
    # Should not reach here, but return best_type as fallback
    return best_type


def get_analysis_type_with_confidence(question: str, use_llm: bool = False) -> Dict[str, any]:
    """
    Detect analysis type and return with confidence score and method used.
    
    Args:
        question: User's question
        use_llm: If True, use LLM for detection when confidence is low
    
    Returns:
        Dictionary with:
        - type: Detected analysis type
        - confidence: Confidence score (0-1)
        - scores: All type scores
        - method: Detection method used ("keyword_high", "keyword_medium", "keyword_strong", "llm", "default")
    """
    scores = detect_analysis_type_keywords(question)
    max_score = max(scores.values())
    total_score = sum(scores.values())
    
    best_type = max(scores, key=scores.get)
    
    # Determine method and confidence
    if max_score >= 2:
        method = "keyword_high"
        confidence = 0.95  # High confidence
    elif max_score == 1:
        if _has_strong_keyword(question, best_type):
            method = "keyword_strong"
            confidence = 0.85  # Strong keyword = reliable
        else:
            method = "keyword_medium"
            confidence = 0.70  # Medium confidence
            
            # If LLM was used, update method and confidence
            if use_llm:
                llm_result = _llm_detect_analysis_type(question)
                if llm_result:
                    method = "llm"
                    confidence = 0.90
                    best_type = llm_result
    else:
        # max_score == 0
        if use_llm:
            llm_result = _llm_detect_analysis_type(question)
            if llm_result:
                method = "llm"
                confidence = 0.85
                best_type = llm_result
            else:
                method = "default"
                confidence = 0.50  # Default fallback
        else:
            method = "default"
            confidence = 0.50  # Default fallback
    
    # Calculate relative confidence if we have scores
    if total_score > 0:
        relative_confidence = max_score / total_score
        # Combine with method-based confidence
        confidence = (confidence + relative_confidence) / 2
    
    return {
        "type": best_type if max_score > 0 or method == "llm" else "explain",
        "confidence": confidence,
        "scores": scores,
        "method": method
    }

