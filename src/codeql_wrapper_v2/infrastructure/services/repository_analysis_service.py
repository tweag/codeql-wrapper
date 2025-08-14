"""Infrastructure implementation of repository analysis service."""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
import logging

from ...domain.entities.analyze_repository_request import AnalyzeRepositoryRequest
from ...domain.entities.analysis_result import RepositoryAnalysisResult, ProjectAnalysisResult
from ...domain.entities.repository import Repository
from ...domain.entities.project import Project
from ...domain.entities.detect_projects_request import DetectProjectsRequest
from ...domain.enumerators.analysis_status import AnalysisStatus
from ...domain.enumerators.language import Language
from ...domain.interfaces.analysis_service import AnalysisService
from ...domain.interfaces.codeql_service import CodeQLService
from ...domain.interfaces.project_detector import ProjectDetector
from ...domain.exceptions.analysis_exceptions import AnalysisError


class ProjectAnalysisServiceImpl(AnalysisService):
    """Infrastructure implementation of repository analysis service using CodeQL CLI directly."""
    
    def __init__(
        self,
        codeql_service: CodeQLService,
        project_detector: ProjectDetector,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize the service with dependencies."""
        self._codeql_service = codeql_service
        self._project_detector = project_detector
        self._logger = logger or logging.getLogger(__name__)
    

    async def analyze_project(self, project: Project, request: AnalyzeRepositoryRequest) -> ProjectAnalysisResult:
        """Analyze project with CodeQL."""
        self._logger.info(f"Analyzing project: {project.name}")
        
        try:
            # Create output directory
            project_output_dir = request.output_directory / project.name
            project_output_dir.mkdir(parents=True, exist_ok=True)
            
            output_files = []
            
            # Get CodeQL executable path
            installation_info = await self._codeql_service.validate_installation()
            if not installation_info.is_installed:
                raise AnalysisError("CodeQL not installed")
            
            codeql_path = installation_info.installation_path
            if not codeql_path:
                # Fallback to 'codeql' command if installation path not available
                codeql_path = "codeql"

            # Analyze each language
            for language in project.detected_languages:
                lang_output_files = await self._analyze_language(
                    project, language, codeql_path, project_output_dir
                )
                output_files.extend(lang_output_files)
            
            return ProjectAnalysisResult(
                project=project,
                status=AnalysisStatus.COMPLETED,
                output_files=output_files
            )
            
        except Exception as e:
            self._logger.error(f"Project analysis failed for {project.name}: {str(e)}")
            return ProjectAnalysisResult(
                project=project,
                status=AnalysisStatus.FAILED,
                error_message=str(e)
            )
    
    async def _analyze_language(
        self, 
        project: Project, 
        language: Language, 
        codeql_path: str, 
        output_dir: Path
    ) -> List[Path]:
        """Analyze a specific language in a project following the old implementation pattern."""
        self._logger.info(f"  Analyzing {language.get_codeql_identifier()} from {project.name}...")
        
        db_path = output_dir / f"db-{language.get_codeql_identifier()}"
        sarif_file = output_dir / f"results-{language.get_codeql_identifier()}.sarif"
        
        try:
            # Step 1: Create database
            await self._create_database(codeql_path, project, language, db_path)
            
            # Step 2: Analyze database
            await self._analyze_database(codeql_path, db_path, sarif_file, language, project.queries)
            
            return  [sarif_file]
            
        except Exception as e:
            self._logger.warning(f"    Failed to analyze {language.get_codeql_identifier()} from {project.name}: {str(e)}")
            return []

    async def _create_database(self, codeql_path: str, project: Project, language: Language, db_path: Path) -> None:
        """Create CodeQL database for a project."""
        lang_id = language.get_codeql_identifier()
        
        cmd = [
            codeql_path, "database", "create",
            str(db_path),
            f"--language={lang_id}",
            f"--source-root={project.project_path}",
            "--force-overwrite"
        ]

        # Only add build-mode if specified and not "none"
        if project.build_mode:
            cmd.append(f"--build-mode={project.build_mode}")
        else:
            cmd.append("--build-mode=none")

        if project.build_script_path:
            cmd.append(f"--command={project.build_script_path}")
        
        self._logger.debug(f"Creating database: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project.project_path
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = f"Database creation failed: {stderr.decode()}"
            self._logger.error(error_msg)
            raise AnalysisError(error_msg)

    async def _analyze_database(self, codeql_path: str, db_path: Path, sarif_file: Path, language: Language, queries: List[str] = []) -> None:
        """Run CodeQL analysis on a database."""
        lang_id = language.get_codeql_identifier()

        if not queries:
            queries = [f"{lang_id}-code-scanning"]


        cmd = [
            codeql_path, "database", "analyze",
            str(db_path),
        ]

        for query in queries:
            cmd.append(query)
        
        cmd.append("--format=sarif-latest")
        cmd.append(f"--output={sarif_file}")

        self._logger.debug(f"Analyzing database: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = f"Database analysis failed: {stderr.decode()}"
            self._logger.error(error_msg)
            raise AnalysisError(error_msg)
 