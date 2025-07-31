"""File system operations abstraction for clean architecture."""

import aiofiles
import aiofiles.os
import shutil
from pathlib import Path
from typing import List, Optional


class FileOperations:
    """
    Abstraction for file system operations.
    
    Provides async file operations while maintaining Clean Architecture
    principles by abstracting infrastructure concerns.
    """
    
    async def read_text_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """Read text content from file asynchronously."""
        async with aiofiles.open(file_path, mode='r', encoding=encoding) as file:
            return await file.read()
    
    async def write_text_file(
        self, 
        file_path: str, 
        content: str, 
        encoding: str = 'utf-8'
    ) -> None:
        """Write text content to file asynchronously."""
        await self.ensure_directory_exists(str(Path(file_path).parent))
        async with aiofiles.open(file_path, mode='w', encoding=encoding) as file:
            await file.write(content)
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists asynchronously."""
        return await aiofiles.os.path.exists(file_path)
    
    async def directory_exists(self, directory_path: str) -> bool:
        """Check if directory exists asynchronously."""
        return await aiofiles.os.path.isdir(directory_path)
    
    async def ensure_directory_exists(self, directory_path: str) -> None:
        """Create directory if it doesn't exist."""
        path = Path(directory_path)
        if not await self.directory_exists(str(path)):
            await aiofiles.os.makedirs(str(path), exist_ok=True)
    
    async def remove_file(self, file_path: str) -> bool:
        """Remove file if it exists."""
        try:
            if await self.file_exists(file_path):
                await aiofiles.os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    async def remove_directory(self, directory_path: str) -> bool:
        """Remove directory and all its contents."""
        try:
            path = Path(directory_path)
            if path.exists():
                shutil.rmtree(str(path))
                return True
            return False
        except Exception:
            return False
    
    async def list_files(
        self, 
        directory_path: str, 
        pattern: Optional[str] = None
    ) -> List[str]:
        """List files in directory, optionally filtered by pattern."""
        try:
            path = Path(directory_path)
            if not await self.directory_exists(str(path)):
                return []
            
            if pattern:
                files = list(path.glob(pattern))
            else:
                files = [f for f in path.iterdir() if f.is_file()]
            
            return [str(f) for f in files]
        except Exception:
            return []
    
    async def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            stat_result = await aiofiles.os.stat(file_path)
            return stat_result.st_size
        except Exception:
            return 0
    
    async def copy_file(self, source_path: str, destination_path: str) -> bool:
        """Copy file from source to destination."""
        try:
            await self.ensure_directory_exists(str(Path(destination_path).parent))
            shutil.copy2(source_path, destination_path)
            return True
        except Exception:
            return False