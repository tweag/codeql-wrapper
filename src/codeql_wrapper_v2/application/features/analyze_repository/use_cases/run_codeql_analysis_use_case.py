"""Use case for running CodeQL analysis."""

from typing import Set
from pathlib import Path

from ....domain.entities.codeql_analysis import (
    CodeQLAnalysisRequest,
    RepositoryAnalysisSummary,
    CodeQLLanguage
)
from ....domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from ....infrastructure.git_utils import GitUtils
from ....infrastructure.logger import get_logger
from ..commands.run_analysis_command import RunAnalysisCommand


class RunCodeQLAnalysisUseCase:
    """Use case for executing end-to-end CodeQL analysis."""
    
    def __init__(self) -> None:
        """Initialize the use case."""
        self._logger = get_logger(__name__)
    
    async def execute(self, command: RunAnalysisCommand) -> RepositoryAnalysisSummary:
        """Execute the complete analysis workflow."""
        try:
            # Convert command to analysis request
            repository_path = Path(command.repository_path)
            
            # Get git information
            git_utils = GitUtils(repository_path)
            git_info = git_utils.get_git_info(
                base_ref=command.base_ref,
                current_ref=command.current_ref
            )
            
            # Convert language strings to CodeQL language enums
            target_languages = None
            if command.languages:
                target_languages = self._parse_languages(command.languages)
            
            # Create analysis request
            request = CodeQLAnalysisRequest(
                repository_path=repository_path,
                git_info=git_info,
                target_languages=target_languages,
                output_directory=Path(command.output_directory) if command.output_directory else None,
                verbose=command.verbose,
                force_install=command.force_install,
                monorepo=command.monorepo,
                max_workers=command.max_workers,
                only_changed_files=command.only_changed_files
            )
            
            # Execute analysis using the domain use case
            analysis_use_case = CodeQLAnalysisUseCase(self._logger)
            result = analysis_use_case.execute(request)
            
            return result
            
        except Exception as e:
            self._logger.error(f"CodeQL analysis failed: {e}")
            raise
    
    def _parse_languages(self, languages: Set[str]) -> Set[CodeQLLanguage]:
        """Parse language strings to CodeQL language enums."""
        target_languages = set()
        
        # Language mapping
        language_mapping = {
            "javascript": CodeQLLanguage.JAVASCRIPT,
            "typescript": CodeQLLanguage.TYPESCRIPT,
            "python": CodeQLLanguage.PYTHON,
            "java": CodeQLLanguage.JAVA,
            "csharp": CodeQLLanguage.CSHARP,
            "cpp": CodeQLLanguage.CPP,
            "go": CodeQLLanguage.GO,
            "ruby": CodeQLLanguage.RUBY,
            "swift": CodeQLLanguage.SWIFT,
            "kotlin": CodeQLLanguage.KOTLIN,
            "actions": CodeQLLanguage.ACTIONS,
        }
        
        for lang in languages:
            lang = lang.strip().lower()
            if lang in language_mapping:
                target_languages.add(language_mapping[lang])
            else:
                self._logger.warning(f"Unsupported language: {lang}")
        
        return target_languages
