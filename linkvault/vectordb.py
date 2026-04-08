"""
SQLite vector database, chunking, embedding, storage, and search.

Stores embeddings as raw float32 blobs in SQLite. Uses cosine similarity
via numpy for search (no extension required).

Embedding model: all-MiniLM-L6-v2 via transformers + torch (384-dim).
"""

import json
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional

import numpy as np

_model = None
_tokenizer = None
EMBED_DIM = 384
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return
    import torch
    from transformers import AutoTokenizer, AutoModel
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    _model = AutoModel.from_pretrained(MODEL_NAME)
    _model.eval()


def embed_texts(texts: List[str]) -> np.ndarray:
    _load_model()
    import torch

    encoded = _tokenizer(
        texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
    )
    with torch.no_grad():
        output = _model(**encoded)
    mask = encoded["attention_mask"].unsqueeze(-1).float()
    embeddings = (output.last_hidden_state * mask).sum(1) / mask.sum(1)
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    return embeddings.cpu().numpy().astype(np.float32)


def embed_text(text: str) -> np.ndarray:
    return embed_texts([text])[0]


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    if not text or len(text) <= max_chars:
        return [text] if text else []

    paragraphs = re.split(r"\n\n+", text)
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current.strip())
            if len(para) > max_chars:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_chars:
                        current = f"{current} {sent}" if current else sent
                    else:
                        if current:
                            chunks.append(current.strip())
                        current = sent
            else:
                current = para

    if current.strip():
        chunks.append(current.strip())

    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(prev_tail + " " + chunks[i])
        chunks = overlapped

    return chunks


def _vec_to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def _blob_to_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT,
    author TEXT,
    full_text TEXT,
    metadata_json TEXT,
    md_path TEXT,
    bundle_path TEXT,
    index_path TEXT,
    public_url TEXT,
    publish_status TEXT,
    publish_error TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding BLOB NOT NULL,
    UNIQUE(doc_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_documents_url ON documents(url);
"""


class VectorDB:
    def __init__(self, db_path: str = "linkvault.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(DB_SCHEMA)
        self._migrate_schema()
        self.conn.commit()

    def _migrate_schema(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(documents)")
        existing = {row[1] for row in cur.fetchall()}
        additions = {
            "bundle_path": "ALTER TABLE documents ADD COLUMN bundle_path TEXT",
            "index_path": "ALTER TABLE documents ADD COLUMN index_path TEXT",
            "public_url": "ALTER TABLE documents ADD COLUMN public_url TEXT",
            "publish_status": "ALTER TABLE documents ADD COLUMN publish_status TEXT",
            "publish_error": "ALTER TABLE documents ADD COLUMN publish_error TEXT",
        }
        for col, sql in additions.items():
            if col not in existing:
                cur.execute(sql)

    def close(self):
        self.conn.close()

    def ingest(
        self,
        url: str,
        source_type: str,
        title: str,
        author: str,
        text: str,
        metadata: dict,
        md_path: str = "",
        bundle_path: str = "",
        index_path: str = "",
        public_url: str = "",
        publish_status: str = "",
        publish_error: str = "",
    ) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM documents WHERE url = ?", (url,))
        row = cur.fetchone()
        values = (
            title,
            author,
            text,
            json.dumps(metadata, ensure_ascii=False),
            md_path,
            bundle_path,
            index_path,
            public_url,
            publish_status,
            publish_error,
        )
        if row:
            doc_id = row[0]
            cur.execute(
                "UPDATE documents SET title=?, author=?, full_text=?, metadata_json=?, md_path=?, bundle_path=?, index_path=?, public_url=?, publish_status=?, publish_error=? WHERE id=?",
                values + (doc_id,),
            )
            cur.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        else:
            cur.execute(
                "INSERT INTO documents (url, source_type, title, author, full_text, metadata_json, md_path, bundle_path, index_path, public_url, publish_status, publish_error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (url, source_type) + values,
            )
            doc_id = cur.lastrowid

        chunks = chunk_text(text)
        if not chunks:
            self.conn.commit()
            return doc_id

        embeddings = embed_texts(chunks)
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            cur.execute(
                "INSERT INTO chunks (doc_id, chunk_index, text, embedding) VALUES (?,?,?,?)",
                (doc_id, i, chunk, _vec_to_blob(emb)),
            )

        self.conn.commit()
        return doc_id

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q_emb = embed_text(query)
        cur = self.conn.cursor()
        cur.execute(
            "SELECT c.id, c.doc_id, c.chunk_index, c.text, c.embedding, d.url, d.title, d.source_type, d.author, d.public_url, d.publish_status "
            "FROM chunks c JOIN documents d ON c.doc_id = d.id"
        )
        scored = []
        for row in cur.fetchall():
            chunk_id, doc_id, chunk_idx, text, emb_blob, url, title, stype, author, public_url, publish_status = row
            emb = _blob_to_vec(emb_blob)
            score = float(np.dot(q_emb, emb))
            scored.append({
                "score": round(score, 4),
                "chunk_text": text[:500],
                "url": url,
                "title": title,
                "source_type": stype,
                "author": author,
                "public_url": public_url,
                "publish_status": publish_status,
                "doc_id": doc_id,
                "chunk_index": chunk_idx,
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def list_documents(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, url, source_type, title, author, md_path, bundle_path, index_path, public_url, publish_status, created_at FROM documents ORDER BY created_at DESC"
        )
        return [
            {
                "id": r[0], "url": r[1], "source_type": r[2], "title": r[3],
                "author": r[4], "md_path": r[5], "bundle_path": r[6], "index_path": r[7],
                "public_url": r[8], "publish_status": r[9], "created_at": r[10]
            }
            for r in cur.fetchall()
        ]

    def get_document_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, url, source_type, title, author, full_text, metadata_json, md_path, bundle_path, index_path, public_url, publish_status, publish_error, created_at FROM documents WHERE url = ?",
            (url,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0], "url": row[1], "source_type": row[2],
            "title": row[3], "author": row[4], "full_text": row[5],
            "metadata": json.loads(row[6]) if row[6] else {},
            "md_path": row[7], "bundle_path": row[8], "index_path": row[9],
            "public_url": row[10], "publish_status": row[11], "publish_error": row[12],
            "created_at": row[13],
        }

    def stats(self) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documents")
        docs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM chunks")
        chunks = cur.fetchone()[0]
        db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        return {"documents": docs, "chunks": chunks, "db_size_bytes": db_size}
