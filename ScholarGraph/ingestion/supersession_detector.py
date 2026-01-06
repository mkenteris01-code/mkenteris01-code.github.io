"""Supersession detector for ScholarGraph."""

import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from core import Neo4jClient
from graph.temporal_schema import TemporalSchemaManager


class SupersessionDetector:
    TITLE_SIMILARITY_THRESHOLD = 0.85
    SESSION_DATE_PATTERN = re.compile(r"session[_-]?(\d{4}[-_]\d{1,2}[-_]\d{1,2})", re.IGNORECASE)

    def __init__(self, neo4j_client: Neo4jClient):
        self.client = neo4j_client
        self.temporal_manager = TemporalSchemaManager(neo4j_client)

    def detect_and_mark_supersession(self, new_document_id: str, new_title: str,
                                      new_file_path: str, new_ingestion_date: str) -> Dict[str, Any]:
        results = {"superseded": [], "reasons": [], "count": 0}
        candidates = self._find_supersession_candidates(
            new_document_id, new_title, new_file_path, new_ingestion_date)
        for candidate in candidates:
            should_supersede, reason = self._should_supersede(
                new_title, new_file_path, new_ingestion_date, candidate)
            if should_supersede:
                old_doc_id = candidate["document_id"]
                self.temporal_manager.mark_document_superseded(
                    document_id=old_doc_id, superseded_by=new_document_id)
                self.temporal_manager.create_supersedes_relationship(
                    newer_document_id=new_document_id, older_document_id=old_doc_id, reason=reason)
                results["superseded"].append({"document_id": old_doc_id, "title": candidate["title"], "reason": reason})
                results["reasons"].append(reason)
        results["count"] = len(results["superseded"])
        return results

    def _find_supersession_candidates(self, new_document_id: str, new_title: str,
                                       new_file_path: str, new_ingestion_date: str) -> List[Dict[str, Any]]:
        new_parent = str(Path(new_file_path).parent).lower()
        session_match = self.SESSION_DATE_PATTERN.search(Path(new_file_path).stem.lower())
        base_name = None
        if session_match:
            base_name = self.SESSION_DATE_PATTERN.sub("", Path(new_file_path).stem.lower()).strip("-_")
        title_prefix = " ".join(new_title.lower().split()[:3])
        query = """MATCH (d:Document)
        WHERE d.document_id <> $new_doc_id AND d.is_latest = true
          AND (d.file_path CONTAINS $parent_dir OR toLower(d.title) STARTS WITH $title_prefix
          OR ($base_name IS NOT NULL AND toLower(d.title) CONTAINS $base_name))
        RETURN d.document_id AS document_id, d.title AS title, d.file_path AS file_path,
               d.ingestion_date AS ingestion_date ORDER BY d.ingestion_date DESC LIMIT 50"""
        try:
            results = self.client.execute_read(query, parameters={
                "new_doc_id": new_document_id, "parent_dir": new_parent,
                "title_prefix": title_prefix, "base_name": base_name})
            return [dict(r) for r in results]
        except Exception as e:
            print(f"Error finding candidates: {e}")
            return []

    def _should_supersede(self, new_title: str, new_file_path: str, new_ingestion_date: str,
                          candidate: Dict[str, Any]) -> Tuple[bool, str]:
        cand_date = candidate.get("ingestion_date", "")
        try:
            new_date = datetime.fromisoformat(new_ingestion_date.replace("Z", "+00:00"))
            cand_dt = datetime.fromisoformat(cand_date.replace("Z", "+00:00")) if cand_date else datetime.min
        except (ValueError, AttributeError):
            new_date, cand_dt = datetime.now(), datetime.min
        if new_date <= cand_dt:
            return False, "newer_document_required"
        if new_title.lower().strip() == candidate.get("title", "").lower().strip():
            return True, "exact_title_match"
        similarity = SequenceMatcher(None, new_title.lower(), candidate.get("title", "").lower()).ratio()
        if similarity >= self.TITLE_SIMILARITY_THRESHOLD:
            return True, f"title_similarity_{similarity:.2f}"
        new_session = self.SESSION_DATE_PATTERN.search(Path(new_file_path).stem)
        cand_session = self.SESSION_DATE_PATTERN.search(Path(candidate.get("file_path", "")).stem)
        if new_session and cand_session:
            new_base = self.SESSION_DATE_PATTERN.sub("", Path(new_file_path).stem).strip("-_")
            cand_base = self.SESSION_DATE_PATTERN.sub("", Path(candidate.get("file_path", "")).stem).strip("-_")
            if new_base.lower() == cand_base.lower():
                return True, "session_document_pattern"
        return False, "no_supersession"

    def retroactively_detect_supersessions(self, dry_run: bool = False) -> Dict[str, Any]:
        results = {"documents_checked": 0, "supersessions_found": 0, "superseded_documents": [], "errors": []}
        query = """MATCH (d:Document) WHERE d.is_latest = true RETURN d.document_id AS document_id,
               d.title AS title, d.file_path AS file_path, d.ingestion_date AS ingestion_date
               ORDER BY d.ingestion_date ASC"""
        try:
            documents = self.client.execute_read(query)
            results["documents_checked"] = len(documents)
            for i, doc in enumerate(documents):
                doc_data = dict(doc)
                for later_doc in documents[i+1:]:
                    later_data = dict(later_doc)
                    should_supersede, reason = self._should_supersede(
                        later_data["title"], later_data["file_path"],
                        later_data["ingestion_date"], doc_data)
                    if should_supersede and "no_supersession" not in reason:
                        if not dry_run:
                            self.temporal_manager.mark_document_superseded(
                                document_id=doc_data["document_id"],
                                superseded_by=later_data["document_id"])
                            self.temporal_manager.create_supersedes_relationship(
                                newer_document_id=later_data["document_id"],
                                older_document_id=doc_data["document_id"], reason=reason)
                        results["superseded_documents"].append({
                            "older": doc_data["title"], "newer": later_data["title"], "reason": reason})
                        results["supersessions_found"] += 1
                        break
        except Exception as e:
            results["errors"].append(str(e))
        return results

    def get_supersession_summary(self) -> Dict[str, Any]:
        query = """MATCH (d:Document) WITH count(d) as total,
            count(CASE WHEN d.is_latest = true THEN 1 END) as latest,
            count(CASE WHEN d.is_latest = false THEN 1 END) as superseded
        OPTIONAL MATCH ()-[r:SUPERSEDES]->() WITH total, latest, superseded, count(r) as rel_count
        RETURN {total_documents: total, latest_versions: latest, superseded_versions: superseded,
                supersession_relationships: rel_count} as summary"""
        try:
            result = self.client.execute_read(query)
            if result:
                return dict(result[0].get("summary", {}))
        except Exception as e:
            print(f"Error getting summary: {e}")
        return {"total_documents": 0, "latest_versions": 0, "superseded_versions": 0, "supersession_relationships": 0}
