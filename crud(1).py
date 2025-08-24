"""
crud.py

A reusable CRUD (Create, Read, Update, Delete) class for MongoDB.
"""

from typing import Any, Dict, List
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class CRUD:
    """Encapsulates CRUD operations for a single MongoDB collection."""

    def __init__(self, uri: str, db_name: str, coll_name: str):
        """Initialize the Mongo client, database, and collection."""
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            self.coll = self.db[coll_name]
        except PyMongoError as e:
            raise ConnectionError(f"Unable to connect to MongoDB: {e}")

    def create(self, document: Dict[str, Any]) -> bool:
        """
        Insert one document.
        Returns True on success, False on failure.
        """
        try:
            result = self.coll.insert_one(document)
            return bool(result.inserted_id)
        except PyMongoError:
            return False

    def read(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find documents matching `query`.
        Returns a list of documents (empty if none).
        """
        try:
            cursor = self.coll.find(query)
            return list(cursor)
        except PyMongoError:
            return []

    def update(self,
               query: Dict[str, Any],
               changes: Dict[str, Any],
               many: bool = False) -> int:
        """
        Update document(s) matching `query`. Uses `$set` on `changes`.
        If `many=True`, calls update_many; else update_one.
        Returns the number of documents modified.
        """
        try:
            if many:
                res = self.coll.update_many(query, {"$set": changes})
            else:
                res = self.coll.update_one(query, {"$set": changes})
            return res.modified_count
        except PyMongoError:
            return 0

    def delete(self,
               query: Dict[str, Any],
               many: bool = False) -> int:
        """
        Delete document(s) matching `query`.
        If `many=True`, calls delete_many; else delete_one.
        Returns the number of documents deleted.
        """
        try:
            if many:
                res = self.coll.delete_many(query)
            else:
                res = self.coll.delete_one(query)
            return res.deleted_count
        except PyMongoError:
            return 0
