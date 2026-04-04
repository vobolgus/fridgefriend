from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Protocol, cast


class _ReadableBody(Protocol):
    async def read(self) -> bytes: ...


class _BodyContextManager(Protocol):
    async def __aenter__(self) -> _ReadableBody: ...

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> object: ...


class _S3Client(Protocol):
    async def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
    ) -> object: ...

    async def get_object(self, *, Bucket: str, Key: str) -> dict[str, _BodyContextManager]: ...

    async def generate_presigned_url(
        self,
        client_method: str,
        *,
        Params: dict[str, str],
        ExpiresIn: int,
    ) -> str: ...


class _S3ClientContextManager(Protocol):
    async def __aenter__(self) -> _S3Client: ...

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> object: ...


class _AiobotocoreSession(Protocol):
    def create_client(
        self,
        service_name: str,
        *,
        endpoint_url: str,
        region_name: str,
    ) -> _S3ClientContextManager: ...


class _AiobotocoreSessionModule(Protocol):
    def get_session(self) -> _AiobotocoreSession: ...


def _get_aiobotocore_session_module() -> _AiobotocoreSessionModule:
    return cast(_AiobotocoreSessionModule, cast(object, import_module("aiobotocore.session")))


class StorageInterface(Protocol):
    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str: ...

    async def download(self, key: str) -> bytes: ...

    async def generate_signed_url(self, key: str, expires_in: int = 3600) -> str: ...


class LocalStorage:
    def __init__(self, base_dir: str = "/tmp/fridgefriend-storage") -> None:
        self._base_dir: Path = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        del content_type
        file_path = self._base_dir / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        _ = file_path.write_bytes(data)
        return key

    async def download(self, key: str) -> bytes:
        file_path = self._base_dir / key
        return file_path.read_bytes()

    async def generate_signed_url(self, key: str, expires_in: int = 3600) -> str:
        del expires_in
        return f"file://{self._base_dir / key}"


class S3Storage:
    def __init__(self, endpoint_url: str, bucket: str, region: str) -> None:
        self._endpoint_url: str = endpoint_url
        self._bucket: str = bucket
        self._region: str = region

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        session_module = _get_aiobotocore_session_module()
        session = session_module.get_session()
        async with session.create_client(
            "s3",
            endpoint_url=self._endpoint_url,
            region_name=self._region,
        ) as client:
            _ = await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return key

    async def download(self, key: str) -> bytes:
        session_module = _get_aiobotocore_session_module()
        session = session_module.get_session()
        async with session.create_client(
            "s3",
            endpoint_url=self._endpoint_url,
            region_name=self._region,
        ) as client:
            response = await client.get_object(Bucket=self._bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def generate_signed_url(self, key: str, expires_in: int = 3600) -> str:
        session_module = _get_aiobotocore_session_module()
        session = session_module.get_session()
        async with session.create_client(
            "s3",
            endpoint_url=self._endpoint_url,
            region_name=self._region,
        ) as client:
            return await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
