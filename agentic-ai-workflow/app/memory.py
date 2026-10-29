"""Memory module - Short-term and long-term memory management.

This module provides:
1. Short-term memory: Redis-backed, for recent conversation context and
   intermediate execution state
2. Long-term memory: PostgreSQL-backed, for persistent storage of completed
   workflows, user profiles, and historical results
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import redis
import psycopg2
from psycopg2.extras import RealDictCursor

from support_ai.schemas import UserRequest

log = logging.getLogger(__name__)


class ShortTermMemory:
    """Redis-backed short-term memory for recent context and intermediate state.
    
    Stores:
    - Recent conversation turns
    - Intermediate plan/execution state
    - Temporary data needed during workflow execution
    - User session context
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        """Initialize the short-term memory.
        
        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
        """
        try:
            self.client = redis.Redis(
                host=host, port=port, db=db, decode_responses=True
            )
            self.client.ping()
            log.info("Short-term memory (Redis) connected successfully")
        except Exception as e:
            log.warning(f"Could not connect to Redis: {e}")
            self.client = None
    
    def _key(self, prefix: str, identifier: str) -> str:
        """Generate a Redis key with prefix."""
        return f"agentic_ai:{prefix}:{identifier}"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = 300) -> bool:
        """Set a value in short-term memory.
        
        Args:
            key: Memory key
            value: Value to store (will be JSON-serialized)
            ttl: Time-to-live in seconds (default: 300s = 5min)
            
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            return self.client.setex(self._key("mem", key), ttl, serialized)
        except Exception as e:
            log.warning(f"Failed to set memory key '{key}': {e}")
            return False
    
    def get(self, key: str) -> Any:
        """Get a value from short-term memory.
        
        Args:
            key: Memory key
            
        Returns:
            Deserialized value or None if not found
        """
        if self.client is None:
            return None
        try:
            key_str = self._key("mem", key)
            value = self.client.get(key_str)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            log.warning(f"Failed to get memory key '{key}': {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from short-term memory."""
        if self.client is None:
            return False
        try:
            return self.client.delete(self._key("mem", key)) > 0
        except Exception as e:
            log.warning(f"Failed to delete memory key '{key}': {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on a memory key."""
        if self.client is None:
            return False
        try:
            return self.client.expire(self._key("mem", key), ttl)
        except Exception as e:
            log.warning(f"Failed to set TTL on key '{key}': {e}")
            return False
    
    def store_conversation(self, session_id: str, role: str, content: str) -> bool:
        """Store a conversation turn.
        
        Args:
            session_id: Unique session identifier
            role: Message role (user, assistant, system)
            content: Message content
            
        Returns:
            True if successful
        """
        key = self._key("conv", session_id)
        message = {"role": role, "content": content}
        try:
            # Append to list, maintaining last 50 messages
            existing = self.get(key) or []
            existing.append(message)
            if len(existing) > 50:
                existing = existing[-50:]  # Keep last 50
            return self.set(key, existing, ttl=86400)  # 24h TTL for conversations
        except Exception as e:
            log.warning(f"Failed to store conversation: {e}")
            return False
    
    def get_conversation(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        key = self._key("conv", session_id)
        messages = self.get(key)
        return messages if messages else []
    
    def store_step_state(self, workflow_id: str, step_id: str, state: Dict[str, Any]) -> bool:
        """Store intermediate state for a workflow step.
        
        Args:
            workflow_id: Unique workflow identifier
            step_id: Step identifier
            state: State dict to store
            
        Returns:
            True if successful
        """
        key = self._key("step", f"{workflow_id}/{step_id}")
        try:
            return self.set(key, state, ttl=600)  # 10min TTL for step state
        except Exception as e:
            log.warning(f"Failed to store step state: {e}")
            return False
    
    def get_step_state(self, workflow_id: str, step_id: str) -> Optional[Dict[str, Any]]:
        """Get intermediate state for a workflow step.
        
        Args:
            workflow_id: Unique workflow identifier
            step_id: Step identifier
            
        Returns:
            State dict or None
        """
        key = self._key("step", f"{workflow_id}/{step_id}")
        return self.get(key)


class LongTermMemory:
    """PostgreSQL-backed long-term memory for persistent storage.
    
    Stores:
    - Completed workflow histories
    - User profiles and preferences
    - Historical search results and analyses
    - Persistent agent memories across sessions
    """
    
    def __init__(
        self, 
        db_name: str = "agentic_ai", 
        user: str = "postgres", 
        password: str = "password",
        host: str = "localhost", 
        port: int = 5432
    ) -> None:
        """Initialize the long-term memory.
        
        Args:
            db_name: PostgreSQL database name
            user: Database username
            password: Database password
            host: Database host
            port: Database port
        """
        self.connection_params = {
            "dbname": db_name,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
        }
        self._connection: Optional[psycopg2.extensions.connection] = None
        self._ensure_tables()
    
    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get or create a database connection."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(**self.connection_params)
                log.info("Long-term memory (PostgreSQL) connected successfully")
            except Exception as e:
                log.error(f"Could not connect to PostgreSQL: {e}")
                raise
        return self._connection
    
    def _ensure_tables(self) -> None:
        """Create required tables if they don't exist."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Table: workflow_history - store completed workflows
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_history (
                        id SERIAL PRIMARY KEY,
                        workflow_id VARCHAR(255) UNIQUE NOT NULL,
                        user_request TEXT NOT NULL,
                        plan_json JSONB,
                        results_json JSONB,
                        verification_json JSONB,
                        final_output TEXT,
                        status VARCHAR(50),
                        created_at TIMESTAMP DEFAULT NOW(),
                        completed_at TIMESTAMP
                    )
                """)
                
                # Table: user_profiles - store user preferences and history
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id VARCHAR(255) PRIMARY KEY,
                        preferences JSONB DEFAULT '{}',
                        search_history JSONB DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Table: search_results - store search results for reference
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS search_results (
                        id SERIAL PRIMARY KEY,
                        query_key VARCHAR(255) NOT NULL,
                        search_query TEXT,
                        results JSONB,
                        retrieved_at TIMESTAMP DEFAULT NOW(),
                        expires_at TIMESTAMP
                    )
                """)
                
                # Index for common search queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_workflow_id 
                    ON workflow_history(workflow_id)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query_key 
                    ON search_results(query_key)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_id 
                    ON user_profiles(user_id)
                """)
                
            conn.commit()
            log.info("Long-term memory tables ensured")
        except Exception as e:
            log.error(f"Failed to ensure tables: {e}")
            conn.rollback()
    
    def _execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a SQL query."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                conn.commit()
                return cur.rowcount
        except Exception as e:
            log.error(f"SQL execution failed: {e}")
            conn.rollback()
            return None
    
    def store_workflow(
        self,
        workflow_id: str,
        user_request: str,
        plan: Dict[str, Any],
        results: Dict[str, Any],
        verification: Dict[str, Any],
        final_output: str,
        status: str = "completed",
    ) -> bool:
        """Store a completed workflow in long-term memory.
        
        Args:
            workflow_id: Unique workflow identifier
            user_request: The original user request
            plan: The execution plan as dict
            results: Tool results as dict
            verification: Verification result as dict
            final_output: The final output text
            status: Workflow status
            
        Returns:
            True if successful
        """
        query = """
            INSERT INTO workflow_history 
            (workflow_id, user_request, plan_json, results_json, verification_json, final_output, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (workflow_id) DO UPDATE SET
                user_request = EXCLUDED.user_request,
                plan_json = EXCLUDED.plan_json,
                results_json = EXCLUDED.results_json,
                verification_json = EXCLUDED.verification_json,
                final_output = EXCLUDED.final_output,
                completed_at = NOW(),
                status = EXCLUDED.status
        """
        try:
            _results = json.dumps(results) if results else "{}"
            _verification = json.dumps(verification) if verification else "{}"
            self._execute(
                query,
                (workflow_id, user_request, json.dumps(plan), _results, _verification, final_output, status),
            )
            log.info(f"Stored workflow {workflow_id} in long-term memory")
            return True
        except Exception as e:
            log.error(f"Failed to store workflow {workflow_id}: {e}")
            return False
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a stored workflow.
        
        Args:
            workflow_id: Unique workflow identifier
            
        Returns:
            Dict with workflow data or None
        """
        query = """
            SELECT * FROM workflow_history 
            WHERE workflow_id = %s
        """
        result = self._execute(query, (workflow_id,))
        if result and len(result) > 0:
            row = result[0]
            return {
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "user_request": row["user_request"],
                "plan": json.loads(row["plan_json"]) if row["plan_json"] else {},
                "results": json.loads(row["results_json"]) if row["results_json"] else {},
                "verification": json.loads(row["verification_json"]) if row["verification_json"] else {},
                "final_output": row["final_output"],
                "status": row["status"],
                "created_at": str(row["created_at"]),
                "completed_at": str(row["completed_at"]) if row["completed_at"] else None,
            }
        return None
    
    def update_user_profile(
        self,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        search_history: Optional[List[str]] = None,
    ) -> bool:
        """Update user profile in long-term memory.
        
        Args:
            user_id: Unique user identifier
            preferences: User preference dict
            search_history: List of search queries
            
        Returns:
            True if successful
        """
        # Get existing profile
        existing = self.get_user_profile(user_id)
        
        if existing:
            # Update existing
            preferences = preferences or existing.get("preferences", {})
            search_history = search_history or existing.get("search_history", [])
            
            # Merge search history (avoid duplicates)
            existing_search = list(existing.get("search_history", []))
            if isinstance(search_history, list):
                for item in search_history:
                    if item not in existing_search:
                        existing_search.append(item)
            search_history = existing_search
            
            preferences_json = json.dumps(preferences) if isinstance(preferences, dict) else "{}"
            search_history_json = json.dumps(search_history) if isinstance(search_history, list) else "[]"
            
            query = """
                UPDATE user_profiles 
                SET preferences = %s, search_history = %s, updated_at = NOW()
                WHERE user_id = %s
            """
            return self._execute(query, (preferences_json, search_history_json, user_id)) > 0
        else:
            # Create new
            preferences_json = json.dumps(preferences) if preferences else "{}"
            search_history_json = json.dumps(search_history) if search_history else "[]"
            
            query = """
                INSERT INTO user_profiles (user_id, preferences, search_history)
                VALUES (%s, %s, %s)
            """
            return self._execute(query, (user_id, preferences_json, search_history_json)) > 0
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from long-term memory.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User profile dict or None
        """
        query = "SELECT * FROM user_profiles WHERE user_id = %s"
        result = self._execute(query, (user_id,))
        if result and len(result) > 0:
            row = result[0]
            profile = {
                "user_id": row["user_id"],
                "preferences": json.loads(row["preferences"]) if row["preferences"] else {},
                "search_history": json.loads(row["search_history"]) if row["search_history"] else [],
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
            }
            return profile
        return None
    
    def store_search_result(
        self,
        query_key: str,
        search_query: str,
        results: Dict[str, Any],
        expires_after_hours: int = 168,  # 1 week default
    ) -> bool:
        """Store search results for future reference.
        
        Args:
            query_key: Unique key for the query (e.g., topic+date_range)
            search_query: The original search query
            results: The search results dict
            expires_after_hours: Hours until expiration
            
        Returns:
            True if successful
        """
        expires_at = None
        # Could calculate expires_at based on expires_after_hours
        
        query = """
            INSERT INTO search_results (query_key, search_query, results, expires_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (query_key) DO UPDATE SET
                search_query = EXCLUDED.search_query,
                results = EXCLUDED.results,
                retrieved_at = NOW(),
                expires_at = EXPIRES.at
        """
        try:
            _results = json.dumps(results) if results else "{}"
            self._execute(
                query,
                (query_key, search_query, _results, expires_at),
            )
            return True
        except Exception as e:
            log.error(f"Failed to store search result: {e}")
            return False
    
    def get_search_result(self, query_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored search results.
        
        Args:
            query_key: Unique key for the query
            
        Returns:
            Search results dict or None
        """
        query = "SELECT * FROM search_results WHERE query_key = %s"
        result = self._execute(query, (query_key,))
        if result and len(result) > 0:
            row = result[0]
            if row["expires_at"] and row["expires_at"] < __import__("datetime").datetime.now():
                # Expired
                return None
            return json.loads(row["results"]) if row["results"] else None
        return None
    
    def close(self) -> None:
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            log.info("Long-term memory connection closed")