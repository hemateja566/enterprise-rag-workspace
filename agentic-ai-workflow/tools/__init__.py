"""Tools module - Search, job search, and skill analysis tools.

This module provides the concrete tool implementations that the agent can
invoke during plan execution. Each tool follows a consistent interface
for compatibility with the executor.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import requests
from datetime import datetime, timezone

log = logging.getLogger(__name__)


class SearchTool:
    """Tool for searching the web using Tavily API."""
    
    def __init__(self, api_key: str = "") -> None:
        """Initialize the search tool.
        
        Args:
            api_key: Tavily API key
        """
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
    
    def search(self, query: str, max_results: int = 10, search_depth: str = "basic") -> Dict[str, Any]:
        """Perform a web search.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced"
            
        Returns:
            Search results dict
        """
        if not self.api_key:
            log.warning("Tavily API key not configured, returning mock results")
            return self._mock_search(query, max_results)
        
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
            }
            response = requests.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"Search API failed: {e}")
            return self._mock_search(query, max_results)
    
    def _mock_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Generate mock search results for demonstration."""
        return {
            "query": query,
            "search_depth": "basic",
            "total_results": max_results,
            "results": [
                {
                    "title": f"Result about {query}",
                    "url": f"https://example.com/result-{i}",
                    "content": f"This is mock content about {query} from result {i}.",
                    "score": 0.9 - i * 0.1,
                }
                for i in range(min(max_results, 5))
            ],
            "raw_content": f"Mock search results for: {query}",
        }


class JobSearchTool:
    """Tool for searching job opportunities from various sources."""
    
    def __init__(self, tavily_tool: SearchTool) -> None:
        """Initialize the job search tool.
        
        Args:
            tavily_tool: Initialized SearchTool instance for web searches
        """
        self.tavily = tavily_tool
    
    def search_jobs(
        self,
        title: str,
        location: str = "Remote",
        skills: Optional[List[str]] = None,
        experience_level: str = "any",
    ) -> Dict[str, Any]:
        """Search for job opportunities matching the criteria.
        
        Args:
            title: Job title to search for
            location: Job location (default: Remote)
            skills: Required skills to filter by
            experience_level: Experience level (entry, mid, senior, any)
            
        Returns:
            Job search results
        """
        query = f"{title} jobs {location}"
        if skills:
            query += f" {', '.join(skills)}"
        if experience_level != "any":
            query += f" {experience_level} level"
        
        results = self.tavily.search(query, max_results=10)
        
        # Extract and format job-relevant information
        jobs = []
        for r in results.get("results", []):
            jobs.append({
                "title": r.get("title", "Unknown"),
                "company": r.get("company", "Unknown"),
                "location": location,
                "url": r.get("url", ""),
                "description": r.get("content", ""),
                "skills": self._extract_skills(r.get("content", "")),
            })
        
        return {
            "query": f"{title} positions in {location}",
            "total_found": len(jobs),
            "jobs": jobs,
            "search_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @staticmethod
    def _extract_skills(text: str) -> List[str]:
        """Extract skill mentions from job description text."""
        # Common AI/ML/tech skills to look for
        skill_keywords = [
            "python", "javascript", "typescript", "machine learning", "deep learning",
            "aws", "gcp", "azure", "docker", "kubernetes", "tensorflow", "pytorch",
            "sql", "git", "agile", "scrum", "data analysis", "data science",
            "react", "node.js", "express", "django", "flask", "fastapi",
            "tensorflow", "scikit-learn", "pandas", "numpy",
        ]
        
        found = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                found.append(skill)
        
        return list(set(found))


class SkillAnalysisTool:
    """Tool for analyzing required skills from job descriptions or user profiles."""
    
    def __init__(self) -> None:
        """Initialize the skill analysis tool."""
        pass
    
    def analyze_skills(
        self, 
        job_descriptions: Optional[List[str]] = None,
        user_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze skills gap between job requirements and user skills.
        
        Args:
            job_descriptions: List of job description texts
            user_skills: List of user's current skills
            
        Returns:
            Skill analysis result with gaps and recommendations
        """
        # Default skill sets if not provided
        default_tech_skills = [
            "python", "javascript", "typescript", "sql", "git",
            "machine learning", "deep learning", "aws", "docker",
        ]
        
        default_user_skills = user_skills or ["python", "sql", "git"]
        
        # Extract skills from job descriptions
        all_job_skills = set(default_tech_skills)
        if job_descriptions:
            for desc in job_descriptions:
                found = self._extract_skills_from_text(desc)
                all_job_skills.update(found)
        
        # Calculate skill gaps
        user_skill_set = set(default_user_skills)
        gaps = all_job_skills - user_skill_set
        overlap = all_job_skills & user_skill_set
        
        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, overlap, all_job_skills)
        
        return {
            "total_job_skills": len(all_job_skills),
            "user_skills": sorted(user_skill_set),
            "required_skills": sorted(all_job_skills),
            "skills_match": sorted(list(overlap)),
            "skill_gaps": sorted(list(gaps)),
            "coverage_ratio": round(len(overlap) / max(len(all_job_skills), 1) * 100, 1),
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @staticmethod
    def _extract_skills_from_text(text: str) -> List[str]:
        """Extract skill mentions from a single text."""
        skill_keywords = [
            "python", "javascript", "typescript", "sql", "git",
            "machine learning", "deep learning", "aws", "docker",
            "tensorflow", "pytorch", "pandas", "numpy", "react",
            "node.js", "express", "django", "flask", "fastapi",
        ]
        
        found = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                found.append(skill)
        
        return found
    
    @staticmethod
    def _generate_recommendations(
        gaps: set,
        overlap: set,
        all_job_skills: set,
    ) -> List[Dict[str, str]]:
        """Generate skill development recommendations."""
        recommendations = []
        
        # Prioritize gaps based on commonality
        priority_skills = [s for s in gaps if s in {"python", "machine learning", "aws"}]
        other_skills = gaps - set(priority_skills)
        
        if priority_skills:
            recommendations.append({
                "priority": "high",
                "action": "Focus on mastering priority skills",
                "details": f"Priority: {', '.join(priority_skills)}",
            })
        
        if other_skills:
            recommendations.append({
                "priority": "medium",
                "action": "Learn additional required skills",
                "details": f"Skills: {', '.join(sorted(other_skills))}",
            })
        
        if not gaps:
            recommendations.append({
                "priority": "low",
                "action": "Maintain and expand existing skills",
                "details": "You have skills covering all identified requirements",
            })
        
        return recommendations