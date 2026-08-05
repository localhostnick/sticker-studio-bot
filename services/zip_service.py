import asyncio
import os
import zipfile
from pathlib import Path
from typing import List, Tuple
from utils.logger import logger

SUPPORTED_STATIC_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_ANIMATED_EXTENSIONS = {".gif", ".webm"}
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_STATIC_EXTENSIONS.union(SUPPORTED_ANIMATED_EXTENSIONS)


class ZipService:
    @classmethod
    async def extract_and_scan_zip(
        cls, 
        zip_path: Path, 
        extract_to_dir: Path
    ) -> List[Path]:
        """Safely extracts a ZIP archive and returns a sorted list of supported media files."""
        extract_to_dir.mkdir(parents=True, exist_ok=True)
        
        loop = asyncio.get_running_loop()
        extracted_files = await loop.run_in_executor(
            None, 
            cls._extract_sync, 
            zip_path, 
            extract_to_dir
        )
        return extracted_files

    @classmethod
    def _extract_sync(cls, zip_path: Path, extract_to_dir: Path) -> List[Path]:
        if not zipfile.is_zipfile(zip_path):
            raise ValueError("Uploaded file is not a valid ZIP archive.")

        valid_media_files: List[Tuple[int, Path]] = []

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            infolist = zip_ref.infolist()
            
            for index, member in enumerate(infolist):
                # Skip directories and system metadata (like __MACOSX)
                if member.is_dir() or "__MACOSX" in member.filename or member.filename.startswith("."):
                    continue

                filename = Path(member.filename).name
                ext = Path(filename).suffix.lower()

                if ext not in ALL_SUPPORTED_EXTENSIONS:
                    logger.debug(f"Skipping unsupported file in ZIP: {member.filename}")
                    continue

                # Zip Slip Protection: Ensure target file is inside extract_to_dir
                target_path = (extract_to_dir / filename).resolve()
                if not str(target_path).startswith(str(extract_to_dir.resolve())):
                    logger.warning(f"Security Alert: Zip Slip attempt detected in member {member.filename}")
                    continue

                # Save file
                with zip_ref.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())

                valid_media_files.append((index, target_path))

        # Sort extracted files by original zip index to preserve order
        valid_media_files.sort(key=lambda x: x[0])
        sorted_files = [path for _, path in valid_media_files]
        
        logger.info(f"Extracted {len(sorted_files)} valid image files from ZIP archive.")
        return sorted_files
