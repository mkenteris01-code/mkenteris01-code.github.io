"""
Batch document ingestion for ScholarGraph.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import time
import os
from datetime import datetime

from core import Neo4jClient, GPURigClient
from graph import NodeManager, RelationshipManager, SchemaManager
from .pdf_processor import PDFProcessor
from .markdown_processor import MarkdownProcessor
from .chunker import TextChunker
from .metadata_extractor import MetadataExtractor
from .supersession_detector import SupersessionDetector


class BatchIngester:
    """Orchestrates batch ingestion of documents into ScholarGraph."""

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        gpu_client: Optional[GPURigClient] = None,
        generate_embeddings: bool = True,
        update_existing: bool = True,
        force_reingestion: bool = False,
        detect_supersession: bool = True
    ):
        self.neo4j_client = neo4j_client
        self.gpu_client = gpu_client
        self.generate_embeddings = generate_embeddings
        self.update_existing = update_existing
        self.force_reingestion = force_reingestion
        self.detect_supersession = detect_supersession
        self.pdf_processor = PDFProcessor()
        self.markdown_processor = MarkdownProcessor()
        self.chunker = TextChunker()
        self.metadata_extractor = MetadataExtractor()
        self.node_manager = NodeManager(neo4j_client)
        self.relationship_manager = RelationshipManager(neo4j_client)
        self.supersession_detector = SupersessionDetector(neo4j_client) if detect_supersession else None
        self.stats = {
            'documents_processed': 0,
            'documents_failed': 0,
            'documents_skipped': 0,
            'documents_updated': 0,
            'documents_superseded': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'topics_created': 0,
            'errors': []
        }

    def check_existing_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        query = """
        MATCH (d:Document {file_path: $file_path})
        RETURN d.document_id AS document_id, d.title AS title,
               d.created_at AS created_at, d.updated_at AS updated_at,
               d.file_modified_at AS file_modified_at LIMIT 1
        """
        results = self.neo4j_client.execute_read(query, parameters={'file_path': file_path})
        return results[0] if results else None

    def should_update_document(self, file_path: str, existing_doc: Dict[str, Any]) -> bool:
        if self.force_reingestion:
            return True
        file_mtime = os.path.getmtime(file_path)
        file_modified_dt = datetime.fromtimestamp(file_mtime)
        stored_mtime = existing_doc.get('file_modified_at')
        if stored_mtime is None:
            return True
        try:
            stored_dt = datetime.fromisoformat(stored_mtime.replace('Z', '+00:00'))
            return file_modified_dt > stored_dt
        except (ValueError, AttributeError):
            return True

    def delete_document_and_chunks(self, document_id: str) -> None:
        query = """
        MATCH (d:Document {document_id: $document_id})
        OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
        OPTIONAL MATCH (d)-[r:DISCUSSES_TOPIC]->()
        DETACH DELETE c, r, d
        """
        self.neo4j_client.execute_write(query, parameters={'document_id': document_id})

    def ingest_document(self, file_path: str, document_type: Optional[str] = None) -> Optional[str]:
        path = Path(file_path)
        if not path.exists():
            self.stats['documents_failed'] += 1
            return None

        absolute_path = str(path.absolute())
        existing_doc = self.check_existing_document(absolute_path)

        if existing_doc:
            if not self.update_existing and not self.force_reingestion:
                self.stats['documents_skipped'] += 1
                return existing_doc['document_id']
            if self.should_update_document(absolute_path, existing_doc):
                self.delete_document_and_chunks(existing_doc['document_id'])
                self.stats['documents_updated'] += 1
            else:
                self.stats['documents_skipped'] += 1
                return existing_doc['document_id']

        if document_type is None:
            if path.suffix.lower() == '.pdf':
                document_type = 'pdf'
            elif path.suffix.lower() in ['.md', '.markdown']:
                document_type = 'markdown'
            else:
                self.stats['documents_failed'] += 1
                return None

        try:
            if document_type == 'pdf':
                doc_data = self.pdf_processor.process_pdf(str(path))
                full_text = doc_data['full_text']
                metadata = doc_data['metadata']
                abstract = doc_data.get('abstract')
            else:
                doc_data = self.markdown_processor.process_markdown(str(path))
                full_text = doc_data['content']
                metadata = doc_data['metadata']
                abstract = doc_data.get('summary')

            extracted_metadata = self.metadata_extractor.extract_all_metadata(
                full_text, title=metadata.get('title')
            )
            topics = extracted_metadata.get('topics', [])
            keywords = extracted_metadata.get('keywords', [])
            concepts = extracted_metadata.get('concepts', [])

            file_mtime = os.path.getmtime(str(path.absolute()))
            file_modified_at = datetime.fromtimestamp(file_mtime).isoformat()
            ingestion_date = datetime.now().isoformat()

            document_id = self.node_manager.create_document_node(
                file_path=str(path.absolute()),
                title=metadata.get('title', path.name),
                document_type=document_type,
                abstract=abstract,
                keywords=keywords,
                authors=metadata.get('authors'),
                date=metadata.get('date') or extracted_metadata.get('extracted_date'),
                doi=metadata.get('doi'),
                metadata=metadata,
                file_modified_at=file_modified_at
            )

            if self.supersession_detector:
                title = metadata.get('title', path.name)
                supersession_results = self.supersession_detector.detect_and_mark_supersession(
                    new_document_id=document_id,
                    new_title=title,
                    new_file_path=str(path.absolute()),
                    new_ingestion_date=ingestion_date
                )
                if supersession_results['count'] > 0:
                    self.stats['documents_superseded'] += supersession_results['count']
                    print(f"  - Superseded {supersession_results['count']} older document(s)")

            chunks = self.chunker.chunk_text_smart(full_text)
            chunk_ids = []
            for chunk in chunks:
                embedding = None
                if self.generate_embeddings and self.gpu_client:
                    try:
                        embedding = self._generate_embedding(chunk.content)
                        self.stats['embeddings_generated'] += 1
                    except Exception:
                        pass

                chunk_id = self.node_manager.create_chunk_node(
                    document_id=document_id,
                    content=chunk.content,
                    position=chunk.position,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    embedding=embedding
                )
                chunk_ids.append(chunk_id)
                self.relationship_manager.create_contains_relationship(document_id, chunk_id)
                self.stats['chunks_created'] += 1

            if len(chunk_ids) > 1:
                self.relationship_manager.link_sequential_chunks(document_id)

            for topic_info in topics:
                self.node_manager.create_topic_node(name=topic_info['name'], category='research')
                self.relationship_manager.create_discusses_topic_relationship(
                    node_id=document_id, node_label='Document', topic_name=topic_info['name'],
                    confidence=topic_info['confidence'], mentions=topic_info['mentions']
                )
                self.stats['topics_created'] += 1

            for concept_info in concepts:
                self.node_manager.create_concept_node(
                    name=concept_info['name'],
                    category=concept_info['type']
                )

            self.stats['documents_processed'] += 1
            return document_id

        except Exception as e:
            self.stats['errors'].append(f"Failed to ingest {file_path}: {str(e)}")
            self.stats['documents_failed'] += 1
            return None

    def ingest_directory(self, directory_path: str, file_pattern: str = "**/*", recursive: bool = True) -> Dict[str, Any]:
        dir_path = Path(directory_path)
        if not dir_path.exists():
            return self.stats

        start_time = time.time()
        pdf_files = list(dir_path.glob(f"{file_pattern}.pdf" if recursive else "*.pdf"))
        md_files = list(dir_path.glob(f"{file_pattern}.md" if recursive else "*.md"))
        md_files.extend(dir_path.glob(f"{file_pattern}.markdown" if recursive else "*.markdown"))
        all_files = pdf_files + md_files

        for file_path in all_files:
            self.ingest_document(str(file_path))

        elapsed_time = time.time() - start_time

        print(f"\n{'='*60}")
        print("Ingestion Summary")
        print(f"{'='*60}")
        print(f"Processed: {self.stats['documents_processed']}")
        print(f"Superseded: {self.stats.get('documents_superseded', 0)}")
        print(f"Failed: {self.stats['documents_failed']}")
        print(f"{'='*60}")

        return self.stats

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        if not self.gpu_client:
            return None
        try:
            return self.gpu_client.generate_embedding(text)
        except Exception:
            return None

    def get_statistics(self) -> Dict[str, Any]:
        return self.stats.copy()

    def reset_statistics(self) -> None:
        self.stats = {
            'documents_processed': 0,
            'documents_failed': 0,
            'documents_skipped': 0,
            'documents_updated': 0,
            'documents_superseded': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'topics_created': 0,
            'errors': []
        }
