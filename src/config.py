"""Configuration management for KEPLER system"""
import os
import json
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class APIConfig:
    """API configuration for external services"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_search_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    bing_search_api_key: Optional[str] = None
    google_vision_api_key: Optional[str] = None


@dataclass
class SystemConfig:
    """System-wide configuration parameters"""
    max_search_results: int = 10
    max_evidence_pieces: int = 20
    relevance_threshold: float = 0.3
    credibility_threshold: float = 0.2
    rank_threshold: float = 0.4
    unknown_domain_credibility: float = 0.5
    min_property_test_iterations: int = 100
    
    # Domain exclusion lists
    fact_checking_domains: List[str] = None
    restricted_domains: List[str] = None
    
    def __post_init__(self):
        if self.fact_checking_domains is None:
            self.fact_checking_domains = [
                "snopes.com",
                "politifact.com",
                "factcheck.org",
                "fullfact.org",
                "checkyourfact.com",
            ]
        if self.restricted_domains is None:
            self.restricted_domains = []


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.api = APIConfig()
        self.system = SystemConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        self.api.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.api.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.api.google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.api.google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.api.bing_search_api_key = os.getenv("BING_SEARCH_API_KEY")
        self.api.google_vision_api_key = os.getenv("GOOGLE_VISION_API_KEY")
        
        # Load system config from env if provided
        if max_results := os.getenv("MAX_SEARCH_RESULTS"):
            self.system.max_search_results = int(max_results)
        if max_evidence := os.getenv("MAX_EVIDENCE_PIECES"):
            self.system.max_evidence_pieces = int(max_evidence)
    
    def load_from_file(self, config_path: str):
        """Load configuration from a JSON file
        
        Args:
            config_path: Path to JSON configuration file
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(path, "r") as f:
            config_data = json.load(f)
        
        # Update API config
        if "api" in config_data:
            for key, value in config_data["api"].items():
                if hasattr(self.api, key):
                    setattr(self.api, key, value)
        
        # Update system config
        if "system" in config_data:
            for key, value in config_data["system"].items():
                if hasattr(self.system, key):
                    setattr(self.system, key, value)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings/errors
        
        Returns:
            List of validation messages (empty if all valid)
        """
        messages = []
        
        # Check for missing API keys (warnings, not errors)
        if not self.api.openai_api_key:
            messages.append("WARNING: OPENAI_API_KEY not set")
        if not self.api.anthropic_api_key:
            messages.append("WARNING: ANTHROPIC_API_KEY not set")
        if not self.api.google_search_api_key:
            messages.append("WARNING: GOOGLE_SEARCH_API_KEY not set")
        
        # Validate system config ranges
        if self.system.max_search_results <= 0:
            messages.append("ERROR: max_search_results must be positive")
        if self.system.max_evidence_pieces <= 0:
            messages.append("ERROR: max_evidence_pieces must be positive")
        if not (0.0 <= self.system.relevance_threshold <= 1.0):
            messages.append("ERROR: relevance_threshold must be between 0 and 1")
        if not (0.0 <= self.system.credibility_threshold <= 1.0):
            messages.append("ERROR: credibility_threshold must be between 0 and 1")
        if not (0.0 <= self.system.rank_threshold <= 1.0):
            messages.append("ERROR: rank_threshold must be between 0 and 1")
        if not (0.0 <= self.system.unknown_domain_credibility <= 1.0):
            messages.append("ERROR: unknown_domain_credibility must be between 0 and 1")
        
        return messages
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            "api": asdict(self.api),
            "system": asdict(self.system),
        }
    
    def save_to_file(self, config_path: str):
        """Save configuration to a JSON file
        
        Args:
            config_path: Path to save configuration file
        """
        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


# Global config instance
config = Config()
