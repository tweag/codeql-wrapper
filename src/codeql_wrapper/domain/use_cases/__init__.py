"""Use cases package for the CodeQL wrapper application."""

from .codeql_analysis_use_case import CodeQLAnalysisUseCase
from .sarif_upload_use_case import SarifUploadUseCase

__all__ = ["CodeQLAnalysisUseCase", "SarifUploadUseCase"]
