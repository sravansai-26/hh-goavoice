import asyncio
from app.models.document import Document, Chunk
from typing import List
import re
import numpy as np
from app.services.embeddings.provider import get_embedding_provider

class ChunkingStrategy:
    async def chunk(self, document: Document) -> List[Chunk]:
        raise NotImplementedError

class FixedChunkingStrategy(ChunkingStrategy):
    def __init__(self, chunk_size: int = 500, overlap: int = 80):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    async def chunk(self, document: Document) -> List[Chunk]:
        chunks = []
        text = document.text
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            chunks.append(Chunk(
                chunk_id=f"{document.document_id}_c{chunk_idx}",
                document_id=document.document_id,
                strategy="fixed",
                text=chunk_text,
                language=document.language,
                start_char=start,
                end_char=min(end, len(text)),
                metadata=document.metadata
            ))
            
            start += (self.chunk_size - self.overlap)
            chunk_idx += 1
            
            if start >= len(text):
                break
                
        return chunks

class SemanticChunkingStrategy(ChunkingStrategy):
    def __init__(self, similarity_threshold: float = 0.5):
        self.similarity_threshold = similarity_threshold
        
    async def chunk(self, document: Document) -> List[Chunk]:
        # Simple sentence splitter for semantic grouping
        sentences = re.split(r'(?<=[.!?]) +', document.text)
        if not sentences:
            return []
            
        embedder = get_embedding_provider()
        
        chunks = []
        current_chunk_sentences = [sentences[0]]
        chunk_idx = 0
        start_char = 0
        
        for i in range(1, len(sentences)):
            # In a real implementation, you'd compare the embedding of current sentence 
            # with the next sentence or the accumulated chunk.
            vec1 = await embedder.embed_query(sentences[i-1])
            vec2 = await embedder.embed_query(sentences[i])
            
            # cosine similarity
            v1_norm = np.linalg.norm(vec1)
            v2_norm = np.linalg.norm(vec2)
            if v1_norm == 0 or v2_norm == 0:
                sim = 0
            else:
                sim = np.dot(vec1, vec2) / (v1_norm * v2_norm)
                
            if sim >= self.similarity_threshold:
                # Same topic, append
                current_chunk_sentences.append(sentences[i])
            else:
                # Topic changed, create chunk
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append(Chunk(
                    chunk_id=f"{document.document_id}_s{chunk_idx}",
                    document_id=document.document_id,
                    strategy="semantic",
                    text=chunk_text,
                    language=document.language,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    metadata=document.metadata
                ))
                start_char += len(chunk_text) + 1 # +1 for space
                chunk_idx += 1
                current_chunk_sentences = [sentences[i]]
                
        # Last chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(Chunk(
                chunk_id=f"{document.document_id}_s{chunk_idx}",
                document_id=document.document_id,
                strategy="semantic",
                text=chunk_text,
                language=document.language,
                start_char=start_char,
                end_char=start_char + len(chunk_text),
                metadata=document.metadata
            ))
            
        return chunks

class MetadataAwareChunkingStrategy(ChunkingStrategy):
    async def chunk(self, document: Document) -> List[Chunk]:
        # Metadata chunking embeds metadata into the chunk text
        # so retrieval models can leverage it
        chunks = []
        text = document.text
        
        # We can reuse fixed chunking but augment text
        chunk_size = 400
        start = 0
        chunk_idx = 0
        
        metadata_str = f"Metadata: [Query ID: {document.metadata.get('query_id', 'N/A')}, Language: {document.language}]\n"
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = metadata_str + text[start:end]
            
            chunks.append(Chunk(
                chunk_id=f"{document.document_id}_m{chunk_idx}",
                document_id=document.document_id,
                strategy="metadata",
                text=chunk_text,
                language=document.language,
                start_char=start,
                end_char=min(end, len(text)),
                metadata=document.metadata
            ))
            
            start += chunk_size
            chunk_idx += 1
            
        return chunks

class HybridChunkingStrategy(ChunkingStrategy):
    def __init__(self, chunk_size: int = 500, overlap: int = 80, similarity_threshold: float = 0.5):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.similarity_threshold = similarity_threshold
        
    async def chunk(self, document: Document) -> List[Chunk]:
        # Hybrid: Split by paragraphs, semantic grouping, max chunk size, and metadata injection
        paragraphs = [p.strip() for p in document.text.split('\n') if p.strip()]
        if not paragraphs:
            return []
            
        embedder = get_embedding_provider()
        chunks = []
        chunk_idx = 0
        start_char = 0
        metadata_str = f"[Query ID: {document.metadata.get('query_id', 'N/A')}] "
        
        current_chunk_paragraphs = [paragraphs[0]]
        current_len = len(paragraphs[0])
        
        for i in range(1, len(paragraphs)):
            vec1 = await embedder.embed_query(paragraphs[i-1])
            vec2 = await embedder.embed_query(paragraphs[i])
            
            v1_norm = np.linalg.norm(vec1)
            v2_norm = np.linalg.norm(vec2)
            sim = 0 if v1_norm == 0 or v2_norm == 0 else np.dot(vec1, vec2) / (v1_norm * v2_norm)
            
            p_len = len(paragraphs[i])
            
            if sim >= self.similarity_threshold and current_len + p_len < self.chunk_size:
                current_chunk_paragraphs.append(paragraphs[i])
                current_len += p_len + 1 # +1 for newline
            else:
                chunk_text = metadata_str + "\n".join(current_chunk_paragraphs)
                chunks.append(Chunk(
                    chunk_id=f"{document.document_id}_h{chunk_idx}",
                    document_id=document.document_id,
                    strategy="hybrid",
                    text=chunk_text,
                    language=document.language,
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    metadata=document.metadata
                ))
                start_char += current_len + 1
                chunk_idx += 1
                
                # Adaptive overlap: carry over last paragraph if it's small, otherwise just start new
                if len(current_chunk_paragraphs[-1]) < self.overlap:
                    current_chunk_paragraphs = [current_chunk_paragraphs[-1], paragraphs[i]]
                    current_len = len(current_chunk_paragraphs[0]) + p_len + 1
                else:
                    current_chunk_paragraphs = [paragraphs[i]]
                    current_len = p_len
                
        if current_chunk_paragraphs:
            chunk_text = metadata_str + "\n".join(current_chunk_paragraphs)
            chunks.append(Chunk(
                chunk_id=f"{document.document_id}_h{chunk_idx}",
                document_id=document.document_id,
                strategy="hybrid",
                text=chunk_text,
                language=document.language,
                start_char=start_char,
                end_char=start_char + len(chunk_text),
                metadata=document.metadata
            ))
            
        return chunks

