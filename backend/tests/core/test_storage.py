from __future__ import annotations

from pathlib import Path

from app.core.storage import LocalStorage, StorageInterface


async def test_local_storage_upload(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=str(tmp_path))
    key = "uploads/test.bin"
    payload = b"hello world"

    returned_key = await storage.upload(key, payload)

    assert returned_key == key
    assert (tmp_path / key).exists()
    assert (tmp_path / key).read_bytes() == payload


async def test_local_storage_download(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=str(tmp_path))
    key = "downloads/test.bin"
    payload = b"download me"

    await storage.upload(key, payload)

    assert await storage.download(key) == payload


async def test_local_storage_generate_signed_url(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=str(tmp_path))

    url = await storage.generate_signed_url("signed/example.txt")

    assert isinstance(url, str)
    assert url.startswith("file://")


def test_storage_interface_protocol() -> None:
    assert getattr(StorageInterface, "_is_protocol", False) is True
