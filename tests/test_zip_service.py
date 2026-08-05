import pytest
import zipfile
from pathlib import Path
from PIL import Image
from services.zip_service import ZipService


@pytest.mark.asyncio
async def test_zip_extraction(tmp_path: Path):
    zip_path = tmp_path / "test.zip"
    
    # Create sample images inside zip
    img1 = Image.new("RGB", (100, 100), color="blue")
    img1_path = tmp_path / "stk1.png"
    img1.save(img1_path)

    img2 = Image.new("RGB", (100, 100), color="red")
    img2_path = tmp_path / "stk2.jpg"
    img2.save(img2_path)

    # Write ZIP
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(img1_path, arcname="01_stk.png")
        zf.write(img2_path, arcname="02_stk.jpg")
        zf.writestr("ignored.txt", "unsupported text file")

    extract_dir = tmp_path / "extracted"
    extracted_files = await ZipService.extract_and_scan_zip(zip_path, extract_dir)

    assert len(extracted_files) == 2
    assert extracted_files[0].name == "01_stk.png"
    assert extracted_files[1].name == "02_stk.jpg"
