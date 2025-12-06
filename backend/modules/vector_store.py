import os, faiss, json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import Dict

# Global registry for in-memory stores (used when privacy mode is enabled)
_in_memory_stores: Dict[str, 'FaissStore'] = {}

class FaissStore:
    # def __init__(self, repo_id: str, base_dir="data/index"):
    #     self.repo_id = repo_id
    #     self.base = Path(base_dir) / repo_id
    #     self.base.mkdir(parents=True, exist_ok=True)
    #     self.meta_path = self.base / "meta.json"
    #     self.index_path = self.base / "faiss.index"
    #     self.model = SentenceTransformer("bge-m3")  # 中文英文都稳
    #     self.index = None
    #     self.metas = []
    def __init__(self, repo_id: str, base_dir: str = "data/index", in_memory: bool = False):
        """
        repo_id  : 用仓库名当索引子目录（例如 'my-portfolio'）
        base_dir : 索引根目录（默认 data/index），app.py 会传入 f"{DATA_DIR}/index"
        in_memory: If True, store in RAM only (no disk writes). Used for privacy mode.
        """
        self.repo_id = repo_id
        self.in_memory = in_memory
        
        if not in_memory:
            # Disk-based storage
            self.base = Path(base_dir) / repo_id
            self.base.mkdir(parents=True, exist_ok=True)
            self.meta_path = self.base / "meta.json"
            self.index_path = self.base / "faiss.index"
        else:
            # In-memory storage (no disk paths)
            self.base = None
            self.meta_path = None
            self.index_path = None
            # Register in global registry
            _in_memory_stores[repo_id] = self

        # 向量模型（中英都稳），用于把代码片段编码成向量
        self.model = SentenceTransformer(r"C:\Users\57811\models\all-MiniLM-L6-v2")
        #self.model = SentenceTransformer("bge-m3")
        #self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        

        self.index = None
        self.metas = []

    def build(self, chunks):
        embeds = self.model.encode([c["snippet"] for c in chunks], normalize_embeddings=True)
        d = embeds.shape[1]
        self.index = faiss.IndexFlatIP(d)  # 点积=余弦（归一化后）
        self.index.add(embeds.astype(np.float32))
        self.metas = chunks
        
        # Only write to disk if not in-memory mode
        if not self.in_memory:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(self.metas, f, ensure_ascii=False)
        else:
            print(f"[vector_store] Index built in-memory for {self.repo_id} ({len(chunks)} chunks)")
    
    def add_chunks(self, chunks):
        """Add new chunks to existing index (incremental update)."""
        if not chunks:
            return
        
        if self.index is None:
            # No existing index, build from scratch
            self.build(chunks)
            return
        
        # Encode new chunks
        new_embeds = self.model.encode([c["snippet"] for c in chunks], normalize_embeddings=True)
        
        # Add to index
        self.index.add(new_embeds.astype(np.float32))
        
        # Add to metas
        self.metas.extend(chunks)
        
        # Only write to disk if not in-memory mode
        if not self.in_memory:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(self.metas, f, ensure_ascii=False)
    
    def remove_chunks_by_file(self, file_path: str):
        """Remove all chunks from a specific file (for file updates/deletes)."""
        if self.index is None:
            return
        
        # Find chunks to remove
        indices_to_remove = []
        for i, meta in enumerate(self.metas):
            if meta.get("file") == file_path or str(meta.get("file")) == str(file_path):
                indices_to_remove.append(i)
        
        if not indices_to_remove:
            return
        
        # Rebuild index without removed chunks
        remaining_metas = [m for i, m in enumerate(self.metas) if i not in indices_to_remove]
        
        if remaining_metas:
            # Rebuild index
            embeds = self.model.encode([c["snippet"] for c in remaining_metas], normalize_embeddings=True)
            d = embeds.shape[1]
            self.index = faiss.IndexFlatIP(d)
            self.index.add(embeds.astype(np.float32))
            self.metas = remaining_metas
        else:
            # All chunks removed, create empty index
            if self.metas:
                sample_embed = self.model.encode(["dummy"], normalize_embeddings=True)
                d = sample_embed.shape[1]
                self.index = faiss.IndexFlatIP(d)
            self.metas = []
        
        # Only write to disk if not in-memory mode
        if not self.in_memory:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(self.metas, f, ensure_ascii=False)
    
    def update_file_chunks(self, file_path: str, new_chunks):
        """Update chunks for a specific file (remove old, add new)."""
        # Remove old chunks
        self.remove_chunks_by_file(file_path)
        # Add new chunks
        if new_chunks:
            self.add_chunks(new_chunks)

    def load(self):
        """Load index from disk (only works if not in-memory)."""
        if self.in_memory:
            raise ValueError("Cannot load in-memory index from disk. In-memory stores are ephemeral.")
        
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index not found: {self.index_path}")
        
        self.index = faiss.read_index(str(self.index_path))
        self.metas = json.load(open(self.meta_path, "r", encoding="utf-8"))

    def query(self, text: str, k: int = 40):
        emb = self.model.encode([text], normalize_embeddings=True).astype(np.float32)
        D, I = self.index.search(emb, k)
        out = []
        for idx, score in zip(I[0], D[0]):
            m = self.metas[int(idx)]
            m2 = dict(m); m2["score_vec"] = float(score)
            out.append(m2)
        return out
