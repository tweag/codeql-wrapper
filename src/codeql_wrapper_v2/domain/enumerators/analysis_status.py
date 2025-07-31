"""Analysis status enumeration for tracking CodeQL analysis lifecycle."""

from enum import Enum, auto


class AnalysisStatus(Enum):
    """Represents the current status of a CodeQL analysis."""
    
    PENDING = auto()
    INITIALIZING = auto()
    BUILDING_DATABASE = auto()
    RUNNING_QUERIES = auto()
    PROCESSING_RESULTS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    
    def is_terminal(self) -> bool:
        """Check if this status represents a terminal state."""
        return self in {
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED,
            AnalysisStatus.CANCELLED
        }
    
    def is_running(self) -> bool:
        """Check if this status represents an active analysis."""
        return self in {
            AnalysisStatus.INITIALIZING,
            AnalysisStatus.BUILDING_DATABASE,
            AnalysisStatus.RUNNING_QUERIES,
            AnalysisStatus.PROCESSING_RESULTS
        }
    
    def can_transition_to(self, target_status: 'AnalysisStatus') -> bool:
        """Validate if transition to target status is allowed."""
        valid_transitions = {
            AnalysisStatus.PENDING: {
                AnalysisStatus.INITIALIZING,
                AnalysisStatus.CANCELLED
            },
            AnalysisStatus.INITIALIZING: {
                AnalysisStatus.BUILDING_DATABASE,
                AnalysisStatus.FAILED,
                AnalysisStatus.CANCELLED
            },
            AnalysisStatus.BUILDING_DATABASE: {
                AnalysisStatus.RUNNING_QUERIES,
                AnalysisStatus.FAILED,
                AnalysisStatus.CANCELLED
            },
            AnalysisStatus.RUNNING_QUERIES: {
                AnalysisStatus.PROCESSING_RESULTS,
                AnalysisStatus.FAILED,
                AnalysisStatus.CANCELLED
            },
            AnalysisStatus.PROCESSING_RESULTS: {
                AnalysisStatus.COMPLETED,
                AnalysisStatus.FAILED,
                AnalysisStatus.CANCELLED
            },
            # Terminal states cannot transition
            AnalysisStatus.COMPLETED: set(),
            AnalysisStatus.FAILED: set(),
            AnalysisStatus.CANCELLED: set()
        }
        
        return target_status in valid_transitions.get(self, set())