import asyncio
from io import BytesIO
from pathlib import Path
from typing import Union, Tuple
from PIL import Image, ImageOps

from utils.logger import logger


class ImageService:
    TARGET_SIZE = 512

    @classmethod
    async def process_sticker_image(
        cls,
        input_source: Union[str, Path, bytes, Image.Image],
        output_path: Union[str, Path],
        target_format: str = "WEBP",
        exact_canvas_512: bool = True,
        add_outline: bool = False,
        outline_width: int = 6
    ) -> Path:
        """Processes an image for Telegram sticker compatibility.
        
        - Preserves aspect ratio
        - Resizes so max dimension is 512
        - Optional Telegram-style white outline border
        - Centers on 512x512 transparent canvas if exact_canvas_512 is True
        - Saves as target_format (WEBP or PNG) with high quality
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, 
            cls._process_sync, 
            input_source, 
            output_path, 
            target_format, 
            exact_canvas_512,
            add_outline,
            outline_width
        )
        return output_path

    @classmethod
    def _process_sync(
        cls,
        input_source: Union[str, Path, bytes, Image.Image],
        output_path: Path,
        target_format: str,
        exact_canvas_512: bool,
        add_outline: bool = False,
        outline_width: int = 6
    ) -> None:
        if isinstance(input_source, (str, Path)):
            img = Image.open(input_source)
        elif isinstance(input_source, bytes):
            img = Image.open(BytesIO(input_source))
        elif isinstance(input_source, Image.Image):
            img = input_source.copy()
        else:
            raise ValueError(f"Unsupported image input type: {type(input_source)}")

        # Convert image to RGBA for transparency support
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Handle EXIF orientation if present
        img = ImageOps.exif_transpose(img)

        width, height = img.size
        if width <= 0 or height <= 0:
            raise ValueError("Invalid image dimensions")

        # Calculate aspect-ratio scaling
        if width > height:
            new_w = cls.TARGET_SIZE
            new_h = max(1, int(round(height * (cls.TARGET_SIZE / width))))
        else:
            new_h = cls.TARGET_SIZE
            new_w = max(1, int(round(width * (cls.TARGET_SIZE / height))))

        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        if add_outline:
            from PIL import ImageFilter
            alpha = img_resized.split()[3]
            filter_size = max(3, outline_width * 2 + 1)
            dilated = alpha.filter(ImageFilter.MaxFilter(filter_size))
            outline = Image.new("RGBA", img_resized.size, (255, 255, 255, 255))
            outline.putalpha(dilated)
            outline.paste(img_resized, (0, 0), mask=img_resized)
            img_resized = outline

        if exact_canvas_512:
            # Create a 512x512 transparent canvas and paste centered
            canvas = Image.new("RGBA", (cls.TARGET_SIZE, cls.TARGET_SIZE), (0, 0, 0, 0))
            offset_x = (cls.TARGET_SIZE - new_w) // 2
            offset_y = (cls.TARGET_SIZE - new_h) // 2
            canvas.paste(img_resized, (offset_x, offset_y), mask=img_resized)
            final_img = canvas
        else:
            final_img = img_resized

        # Save output
        save_fmt = target_format.upper()
        if save_fmt not in ("WEBP", "PNG"):
            save_fmt = "WEBP"

        final_img.save(
            output_path,
            format=save_fmt,
            quality=95,
            optimize=True
        )
        logger.debug(f"Processed sticker image saved to {output_path} ({save_fmt})")

    @classmethod
    async def create_thumbnail(
        cls,
        first_sticker_path: Union[str, Path],
        output_thumb_path: Union[str, Path]
    ) -> Path:
        """Creates a 100x100 thumbnail for sticker pack cover if needed."""
        output_thumb_path = Path(output_thumb_path)
        output_thumb_path.parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_running_loop()
        def _thumb_sync():
            img = Image.open(first_sticker_path)
            img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            img.save(output_thumb_path, format="PNG")

        await loop.run_in_executor(None, _thumb_sync)
        return output_thumb_path
