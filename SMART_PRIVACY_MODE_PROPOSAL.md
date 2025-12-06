# Smart Privacy Mode: Analysis & Proposals

## 🤔 Current Approach (Manual Selection)

**How it works now:**
- User manually enables/disables privacy mode globally
- All repositories use the same mode (privacy ON or OFF)
- Binary choice: everything in RAM or everything on disk

**Problems:**
- ❌ One-size-fits-all (all repos treated the same)
- ❌ User must manually decide
- ❌ Can't mix modes (some repos private, some public)
- ❌ No intelligence about what needs privacy

## 💡 Proposed Approaches

### **Approach 1: Per-Repository Privacy Mode** ⭐ (RECOMMENDED)

**Concept:**
- Each repository can have its own privacy setting
- Some repos use RAM (private), others use disk (public)
- User sets privacy per repo, not globally

**How it works:**
```python
# User indexes repo with privacy flag
POST /index_repo {
  "repo_dir": "/my/private/project",
  "privacy_mode": true  # This repo only
}

POST /index_repo {
  "repo_dir": "/my/public/project", 
  "privacy_mode": false  # This repo only
}
```

**Benefits:**
- ✅ Flexible: Mix private and public repos
- ✅ Granular control: Per-repo settings
- ✅ Smart defaults: Auto-detect based on repo location/name
- ✅ User-friendly: Set once per repo

**Implementation:**
- Store privacy preference per repo (in metadata)
- Each repo's index uses its own storage mode
- Search/chat respects each repo's privacy setting

---

### **Approach 2: Content-Based Auto-Detection** 🔍

**Concept:**
- System analyzes code for sensitive information
- Automatically uses privacy mode if secrets detected
- No user decision needed

**How it works:**
```python
# System analyzes code before indexing
def analyze_sensitivity(code):
    sensitive_patterns = [
        r'api[_-]?key\s*=\s*["\']([^"\']+)["\']',
        r'password\s*=\s*["\']([^"\']+)["\']',
        r'secret\s*=\s*["\']([^"\']+)["\']',
        r'private[_-]?key',
        r'\.env',  # Environment files
    ]
    
    if any(pattern in code for pattern in sensitive_patterns):
        return "sensitive"  # Use privacy mode
    return "normal"  # Use disk storage
```

**Benefits:**
- ✅ Automatic: No user decision needed
- ✅ Smart: Detects sensitive code
- ✅ Secure: Protects secrets automatically

**Limitations:**
- ⚠️ May have false positives (detects "api_key" even if not real)
- ⚠️ May miss some sensitive patterns
- ⚠️ Privacy is about user preference, not just secrets

---

### **Approach 3: Hybrid Mode (Best of Both)** 🎯

**Concept:**
- Combine per-repo privacy + auto-detection + smart defaults
- Most flexible and intelligent approach

**How it works:**
```python
def determine_storage_mode(repo_dir, user_preference=None):
    # 1. Check user preference (if explicitly set)
    if user_preference is not None:
        return user_preference
    
    # 2. Check repo location patterns
    if is_private_location(repo_dir):
        return "privacy"  # Auto-enable for private folders
    
    # 3. Analyze code for sensitive content
    if contains_sensitive_code(repo_dir):
        return "privacy"  # Auto-enable for sensitive code
    
    # 4. Check repo name patterns
    if is_private_repo_name(repo_dir):
        return "privacy"  # Auto-enable for "private", "secret" repos
    
    # 5. Default to disk storage
    return "normal"
```

**Smart Defaults:**
- `~/private/`, `~/secret/` → Privacy mode
- `~/public/`, `~/projects/` → Normal mode
- Repos with `.env`, `secrets/` → Privacy mode
- Repos with `api_key`, `password` in code → Privacy mode

**Benefits:**
- ✅ Intelligent: Auto-detects privacy needs
- ✅ Flexible: User can override
- ✅ Secure: Protects sensitive code automatically
- ✅ User-friendly: Works out of the box

---

### **Approach 4: Question-Based Analysis** ❓

**Concept:**
- Analyze user's question/request
- Choose privacy mode based on question sensitivity

**How it works:**
```python
def analyze_question_sensitivity(question):
    sensitive_keywords = [
        "password", "secret", "api key", "private",
        "authentication", "security", "credential"
    ]
    
    if any(keyword in question.lower() for keyword in sensitive_keywords):
        return "privacy"  # Use RAM for sensitive questions
    return "normal"  # Use disk for normal questions
```

**Problems:**
- ❌ Privacy is about CODE storage, not question type
- ❌ Question sensitivity ≠ code sensitivity
- ❌ User might ask about public code but want privacy
- ❌ Doesn't make much sense

**Verdict:** ❌ Not recommended - question type doesn't determine storage needs

---

## 🎯 Recommended Solution: Hybrid Approach

### **Best Approach: Per-Repo Privacy + Smart Defaults**

**Why this is best:**
1. **Privacy is per-repository, not per-question**
   - Some repos are private (personal projects)
   - Some repos are public (open source)
   - User wants different privacy for different repos

2. **Smart defaults reduce user burden**
   - Auto-detect private folders (`~/private/`)
   - Auto-detect sensitive code (API keys, passwords)
   - User can override if needed

3. **Flexible and user-friendly**
   - Works automatically (smart defaults)
   - User can customize (per-repo settings)
   - Mix private and public repos

### **Implementation Plan:**

#### **Phase 1: Per-Repository Privacy**
```python
# Store privacy preference per repo
repo_privacy_settings = {
    "repo_id_1": {"privacy_mode": True},   # Private repo
    "repo_id_2": {"privacy_mode": False},  # Public repo
}
```

#### **Phase 2: Smart Defaults**
```python
def get_repo_privacy_mode(repo_dir, explicit_setting=None):
    # 1. Use explicit setting if provided
    if explicit_setting is not None:
        return explicit_setting
    
    # 2. Check repo location
    if "/private/" in repo_dir or "/secret/" in repo_dir:
        return True  # Auto-enable for private folders
    
    # 3. Check repo name
    repo_name = Path(repo_dir).name.lower()
    if any(word in repo_name for word in ["private", "secret", "personal"]):
        return True
    
    # 4. Check for sensitive files
    if (Path(repo_dir) / ".env").exists():
        return True  # Has environment file
    
    # 5. Default to global privacy mode
    return get_privacy_mode().is_enabled()
```

#### **Phase 3: Content Analysis (Optional)**
```python
def detect_sensitive_code(repo_dir):
    """Scan code for sensitive patterns."""
    sensitive_patterns = [
        r'api[_-]?key\s*=',
        r'password\s*=',
        r'secret\s*=',
        r'private[_-]?key',
    ]
    
    for file in scan_repo(repo_dir):
        if any(re.search(pattern, file.content, re.IGNORECASE) 
               for pattern in sensitive_patterns):
            return True
    return False
```

## 📊 Comparison Table

| Approach | Intelligence | Flexibility | User Control | Complexity |
|----------|-------------|------------|--------------|------------|
| **Current (Global)** | ❌ None | ❌ Low | ✅ Full | ✅ Simple |
| **Per-Repo Privacy** | ⚠️ Medium | ✅ High | ✅ Full | ⚠️ Medium |
| **Content Detection** | ✅ High | ❌ Low | ❌ Low | ⚠️ Medium |
| **Hybrid (Recommended)** | ✅ High | ✅ High | ✅ Full | ⚠️ Medium |
| **Question-Based** | ❌ Low | ❌ Low | ❌ Low | ✅ Simple |

## 🚀 Recommended Implementation

**Step 1: Add Per-Repository Privacy Settings**
- Store privacy mode per repo (in metadata)
- Allow setting privacy when indexing: `POST /index_repo {"privacy_mode": true}`

**Step 2: Add Smart Defaults**
- Auto-detect private folders (`~/private/`, `~/secret/`)
- Auto-detect sensitive code (API keys, passwords)
- Auto-detect repo name patterns (`private-*`, `secret-*`)

**Step 3: Hybrid Storage**
- Some repos in RAM (privacy mode)
- Some repos on disk (normal mode)
- Search/chat respects each repo's setting

**Step 4: User Override**
- User can explicitly set privacy per repo
- User can override auto-detection
- User can set global default

## 💭 Example Usage

```bash
# Auto-detected: Private folder → Privacy mode
POST /index_repo {"repo_dir": "~/private/my-secret-project"}
# System: "Detected private folder, using privacy mode"

# Auto-detected: Sensitive code → Privacy mode  
POST /index_repo {"repo_dir": "~/projects/api-service"}
# System: "Detected API keys in code, using privacy mode"

# Explicit setting: Override auto-detection
POST /index_repo {
  "repo_dir": "~/projects/api-service",
  "privacy_mode": false  # User says it's OK to store on disk
}

# Public repo: Normal mode
POST /index_repo {"repo_dir": "~/public/open-source-project"}
# System: "Public repo, using normal disk storage"
```

## ✅ Conclusion

**Best Approach: Per-Repository Privacy + Smart Defaults**

- Privacy is about repositories, not questions
- Smart defaults reduce user burden
- User can override when needed
- Mix private and public repos
- Most flexible and intelligent solution

**Question-based analysis doesn't make sense** because:
- Privacy is about code storage, not question type
- User might ask about public code but want privacy
- Question sensitivity ≠ code sensitivity
