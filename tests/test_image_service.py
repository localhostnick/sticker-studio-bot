import pytest
import asyncio
from pathlib import Path
from PIL import Image
from services.image_service import ImageService


@pytest.mark.asyncio
async def test_image_processing_dimensions(tmp_path: Path):
    # Create a non-square test image (800x400)
    test_img = Image.new("RGB", (800, 400), color=(255, 0, 0))
    src_file = tmp_path / "input.jpg"
    test_img.save(src_file)

    output_file = tmp_path / "output.webp"
    result_path = await ImageService.process_sticker_image(
        input_source=src_file,
        output_path=output_file,
        target_format="WEBP",
        exact_canvas_512=True
    )

    assert result_path.exists()
    
    # Verify resulting canvas is 512x512 with RGBA
    out_img = Image.open(result_path)
    assert out_img.size == (512, 512)
    assert out_img.mode == "RGBA"
