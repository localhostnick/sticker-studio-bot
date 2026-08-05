import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from utils.logger import logger


class AnimatedService:
    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check if ffmpeg command line executable is present on the host system."""
        return shutil.which("ffmpeg") is not None

    @classmethod
    async def process_video_sticker(
        cls,
        input_path: Path,
        output_path: Path
    ) -> Path:
        """Converts GIF/WEBM to Telegram video sticker format (WEBM VP9 512x512, <=3s, no audio, <=256KB)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not cls.is_ffmpeg_available():
            logger.warning("ffmpeg is not installed. Video sticker conversion may be limited.")
            # If input is already webm, return as-is or raise error
            if input_path.suffix.lower() == ".webm":
                shutil.copy(input_path, output_path)
                return output_path
            else:
                raise RuntimeError("ffmpeg executable is required to convert GIF or unformatted videos into Telegram WEBM stickers.")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls._convert_video_sync, input_path, output_path)
        return output_path

    @classmethod
    def _convert_video_sync(cls, input_path: Path, output_path: Path) -> None:
        """Executes ffmpeg command to produce Telegram-compliant VP9 WEBM video sticker."""
        # ffmpeg filter: scale to 512 max while keeping aspect ratio, fps=30, t=3 max, no audio
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-t", "3",  # Max 3 seconds
            "-vf", "scale='if(gt(iw,ih),512,-1)':'if(gt(iw,ih),-1,512)',fps=30,pad=512:512:(512-iw)/2:(512-ih)/2:color=0x00000000",
            "-c:v", "libvpx-vp9",
            "-crf", "30",
            "-b:v", "256k",
            "-an",  # Remove audio
            "-metadata:s:v:0", "alpha_mode=1",
            str(output_path)
        ]

        logger.info(f"Running ffmpeg video conversion: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed to convert video sticker: {result.stderr[-200:]}")
        
        # Check output file size constraint (256 KB)
        file_size = os.path.getsize(output_path)
        if file_size > 256 * 1024:
            logger.warning(f"Video sticker exceeds 256KB limit ({file_size} bytes). Applying stronger compression.")
            # Retry with lower bitrate
            cmd_compress = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-t", "3",
                "-vf", "scale='if(gt(iw,ih),512,-1)':'if(gt(iw,ih),-1,512)',fps=30,pad=512:512:(512-iw)/2:(512-ih)/2:color=0x00000000",
                "-c:v", "libvpx-vp9",
                "-crf", "40",
                "-b:v", "150k",
                "-an",
                str(output_path)
            ]
            subprocess.run(cmd_compress, check=True)
