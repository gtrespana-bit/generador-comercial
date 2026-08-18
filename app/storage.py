"""Almacenamiento privado intercambiable para archivos de CotizaT.

Los modelos guardan referencias ``storage://<object-key>`` y metadatos en
PostgreSQL; nunca guardan el binario. El backend local conserva compatibilidad
y Supabase Storage puede sustituirse posteriormente por R2 sin cambiar los
modelos comerciales.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request as UrlRequest, urlopen
import uuid

from .auth import es_clave_secreta_servidor
from .database import (
    DATABASE_BACKEND,
    DATABASE_IS_SQLITE,
    PRIVATE_STORAGE_DIR,
    UPLOADS_DIR,
)
from .permisos import es_lectura

STORAGE_REFERENCE_PREFIX = "storage://"
DEFAULT_BUCKET = "cotizat-private"
MAX_OBJECT_SIZE = 12 * 1024 * 1024
_ALLOWED_CATEGORIES = {
    "anexos", "comprobantes", "firmas", "fotos-proyecto", "fichas-tecnicas",
    "importaciones", "manifiestos-importacion", "logos", "partidas", "productos",
    "presupuestos",
}


class StorageError(RuntimeError):
    """Fallo seguro de almacenamiento que nunca incluye credenciales."""


class StorageNotConfigured(StorageError):
    pass


class InvalidStorageKey(StorageError):
    pass


@dataclass(frozen=True)
class StorageSettings:
    backend: str
    local_root: Path
    supabase_url: str = ""
    secret_key: str = ""
    bucket: str = DEFAULT_BUCKET

    @classmethod
    def from_environment(cls) -> "StorageSettings":
        configured = os.environ.get("COTIZAT_STORAGE_BACKEND", "").strip().lower()
        backend = configured or ("local" if DATABASE_BACKEND == "sqlite" else "supabase")
        if backend not in {"local", "supabase"}:
            raise StorageNotConfigured("COTIZAT_STORAGE_BACKEND debe ser local o supabase.")
        if backend == "local":
            return cls(backend="local", local_root=PRIVATE_STORAGE_DIR)

        url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
        secret_key = os.environ.get("SUPABASE_SECRET_KEY", "").strip()
        bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", DEFAULT_BUCKET).strip()
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise StorageNotConfigured("SUPABASE_URL no es válida para Storage.")
        if not es_clave_secreta_servidor(secret_key):
            raise StorageNotConfigured(
                "SUPABASE_SECRET_KEY debe usar una clave sb_secret_ "
                "o el JWT service_role legacy, exclusivo del servidor."
            )
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,62}", bucket):
            raise StorageNotConfigured("El nombre del bucket privado no es válido.")
        return cls(
            backend="supabase",
            local_root=PRIVATE_STORAGE_DIR,
            supabase_url=url,
            secret_key=secret_key,
            bucket=bucket,
        )


@dataclass(frozen=True)
class StoredObject:
    reference: str
    object_key: str
    backend: str
    bucket: str
    content_type: str
    size: int
    sha256: str


def validate_object_key(value: str) -> str:
    key = str(value or "").strip()
    path = PurePosixPath(key)
    if (
        not key
        or key.startswith("/")
        or "\\" in key
        or key.endswith("/")
        or "//" in key
        or any(part in {"", ".", ".."} for part in path.parts)
        or any(ord(char) < 32 for char in key)
        or not re.fullmatch(r"[A-Za-z0-9._~/-]+", key)
        or len(key) > 900
    ):
        raise InvalidStorageKey("La clave del objeto no es válida.")
    return path.as_posix()


def validate_tenant_object_key(object_key: str, organization_id: int) -> str:
    key = validate_object_key(object_key)
    try:
        organization_id = int(organization_id)
    except (TypeError, ValueError) as exc:
        raise InvalidStorageKey("La organización del objeto no es válida.") from exc
    if organization_id <= 0 or not key.startswith(f"organizaciones/{organization_id}/"):
        raise InvalidStorageKey("La clave no pertenece a la organización activa.")
    return key


def storage_reference(object_key: str) -> str:
    return STORAGE_REFERENCE_PREFIX + validate_object_key(object_key)


def object_key_from_reference(reference: str) -> str | None:
    value = str(reference or "").strip()
    if not value.startswith(STORAGE_REFERENCE_PREFIX):
        return None
    return validate_object_key(value[len(STORAGE_REFERENCE_PREFIX):])


def file_url(reference: str, download: bool = False) -> str:
    """URL autenticada para referencias nuevas y estática para legado local."""
    value = str(reference or "").strip()
    key = object_key_from_reference(value)
    if key is not None:
        url = "/archivos/" + quote(key, safe="/")
        return url + ("?download=1" if download else "")
    clean = value.lstrip("/")
    if clean.startswith("static/uploads/"):
        clean = clean[7:]
    elif clean.startswith("static/"):
        return "/" + clean
    suffix = "?download=1" if download else ""
    if clean.startswith("uploads/"):
        if DATABASE_IS_SQLITE:
            return "/static/" + clean + suffix
        return "/archivos-legado/" + quote(clean[8:], safe="/") + suffix
    if clean.startswith("importaciones/"):
        if DATABASE_IS_SQLITE:
            return "/static/uploads/" + clean + suffix
        return "/archivos-legado/" + quote(clean, safe="/") + suffix
    return "/static/" + clean if clean else ""


class StorageBackend(ABC):
    name: str
    bucket: str

    @abstractmethod
    def put(self, object_key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self, object_key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, object_key: str) -> None:
        raise NotImplementedError

    def copy(self, source_key: str, destination_key: str, content_type: str) -> None:
        self.put(destination_key, self.read(source_key), content_type)

    def list(self, prefix: str = "") -> list[str]:
        """Claves de objetos bajo un prefijo (usado por el respaldo automático).

        No es abstracto a propósito: los backends que no lo soporten fallan al
        **usarlo**, no al instanciarse. Implementado en LocalStorage y
        SupabaseStorage (E4-021).
        """
        raise NotImplementedError("Este backend de almacenamiento no permite listar objetos.")

    def local_path(self, object_key: str) -> Path | None:
        return None


class LocalStorage(StorageBackend):
    name = "local"
    bucket = "local"

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass

    def _path(self, object_key: str) -> Path:
        key = validate_object_key(object_key)
        path = (self.root / key).resolve()
        if path == self.root or self.root not in path.parents:
            raise InvalidStorageKey("La clave sale del almacenamiento permitido.")
        return path

    def put(
        self,
        object_key: str,
        data: bytes,
        content_type: str,
        max_size: int | None = None,  # noqa: ARG002
    ) -> None:
        limite = max_size or MAX_OBJECT_SIZE
        if not data or len(data) > limite:
            raise StorageError(f"El objeto está vacío o supera {limite // (1024 * 1024)} MB.")
        path = self._path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        current = path.parent
        while current == self.root or self.root in current.parents:
            try:
                os.chmod(current, 0o700)
            except OSError:
                pass
            if current == self.root:
                break
            current = current.parent
        temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex[:8])
        try:
            temporary.write_bytes(data)
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def read(self, object_key: str) -> bytes:
        path = self._path(object_key)
        try:
            data = path.read_bytes()
        except FileNotFoundError as exc:
            raise StorageError("El archivo solicitado no existe.") from exc
        if len(data) > MAX_OBJECT_SIZE:
            raise StorageError("El objeto supera el tamaño permitido.")
        return data

    def delete(self, object_key: str) -> None:
        self._path(object_key).unlink(missing_ok=True)

    def list(self, prefix: str = "") -> list[str]:
        """Claves existentes bajo ``prefix`` (ordenadas, relativas a la raíz)."""
        base = ""
        if prefix:
            base = validate_object_key(prefix.rstrip("/")) + "/"
        raiz = self.root
        claves = []
        for ruta in raiz.rglob("*"):
            if not ruta.is_file():
                continue
            clave = ruta.relative_to(raiz).as_posix()
            if clave.startswith(base):
                claves.append(clave)
        return sorted(claves)

    def local_path(self, object_key: str) -> Path | None:
        path = self._path(object_key)
        return path if path.is_file() else None


class SupabaseStorage(StorageBackend):
    name = "supabase"

    def __init__(self, settings: StorageSettings):
        self.settings = settings
        self.bucket = settings.bucket

    def _request(
        self,
        method: str,
        path: str,
        data: bytes | None = None,
        content_type: str = "application/json",
        extra_headers: dict[str, str] | None = None,
        expected: set[int] | None = None,
    ) -> bytes:
        # sb_secret_ es opaca, no JWT: solo va en apikey, nunca como Bearer.
        headers = {"apikey": self.settings.secret_key, "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = content_type
        headers.update(extra_headers or {})
        request = UrlRequest(
            self.settings.supabase_url + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310 (URL validada)
                result = response.read(MAX_OBJECT_SIZE + 1)
                if expected and response.status not in expected:
                    raise StorageError("Supabase Storage rechazó la operación.")
                return result
        except HTTPError as exc:
            if exc.code == 404:
                raise StorageError("El objeto o bucket privado no existe.") from exc
            raise StorageError("Supabase Storage rechazó la operación.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise StorageError("No se pudo contactar con Supabase Storage.") from exc

    def put(
        self,
        object_key: str,
        data: bytes,
        content_type: str,
        max_size: int | None = None,
    ) -> None:
        limite = max_size or MAX_OBJECT_SIZE
        if not data or len(data) > limite:
            raise StorageError(f"El objeto está vacío o supera {limite // (1024 * 1024)} MB.")
        key = quote(validate_object_key(object_key), safe="/")
        bucket = quote(self.bucket, safe="")
        self._request(
            "POST", f"/storage/v1/object/{bucket}/{key}", data=data,
            content_type=content_type,
            extra_headers={"x-upsert": "false", "cache-control": "3600"},
            expected={200},
        )

    def read(self, object_key: str) -> bytes:
        key = quote(validate_object_key(object_key), safe="/")
        bucket = quote(self.bucket, safe="")
        data = self._request("GET", f"/storage/v1/object/{bucket}/{key}", expected={200})
        if len(data) > MAX_OBJECT_SIZE:
            raise StorageError("El objeto supera el tamaño permitido.")
        return data

    def delete(self, object_key: str) -> None:
        key = validate_object_key(object_key)
        bucket = quote(self.bucket, safe="")
        self._request(
            "DELETE", f"/storage/v1/object/{bucket}",
            data=json.dumps({"prefixes": [key]}).encode("utf-8"), expected={200},
        )

    def list(self, prefix: str = "") -> list[str]:
        """Claves de objetos bajo ``prefix`` vía el endpoint de listado.

        El listado de Supabase Storage devuelve carpetas (``id: null``) y
        objetos; solo se conservan los objetos, con su clave completa.
        """
        prefijo = validate_object_key(prefix.rstrip("/")) if prefix else ""
        bucket = quote(self.bucket, safe="")
        raw = self._request(
            "POST", f"/storage/v1/object/list/{bucket}",
            data=json.dumps({
                "prefix": prefijo + "/" if prefijo else "",
                "limit": 1000,
                "offset": 0,
            }).encode("utf-8"),
            expected={200},
        )
        try:
            items = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise StorageError("Supabase Storage devolvió un listado no válido.") from exc
        if not isinstance(items, list):
            raise StorageError("Supabase Storage devolvió un listado no válido.")
        claves = []
        for item in items:
            if not isinstance(item, dict) or item.get("id") is None:
                continue  # carpeta
            nombre = str(item.get("name") or "")
            if nombre:
                claves.append(prefijo + nombre)
        return sorted(claves)

    def bucket_status(self) -> dict[str, Any] | None:
        bucket = quote(self.bucket, safe="")
        try:
            raw = self._request("GET", f"/storage/v1/bucket/{bucket}", expected={200})
        except StorageError as exc:
            if "no existe" in str(exc):
                return None
            raise
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise StorageError("Supabase Storage devolvió una respuesta no válida.") from exc
        return value if isinstance(value, dict) else None

    def create_private_bucket(self) -> None:
        """Crea el bucket explícitamente; nunca se invoca al arrancar la app."""
        payload = {
            "id": self.bucket,
            "name": self.bucket,
            "public": False,
            "file_size_limit": MAX_OBJECT_SIZE,
            "allowed_mime_types": [
                "image/jpeg", "image/png", "image/webp", "image/gif",
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/json",
                # E4-021: los respaldos automáticos se guardan como .zip.
                "application/zip",
            ],
        }
        self._request(
            "POST", "/storage/v1/bucket",
            data=json.dumps(payload).encode("utf-8"), expected={200},
        )


@lru_cache(maxsize=1)
def get_storage_backend() -> StorageBackend:
    settings = StorageSettings.from_environment()
    if settings.backend == "local":
        return LocalStorage(settings.local_root)
    return SupabaseStorage(settings)


def reset_storage_backend_cache() -> None:
    get_storage_backend.cache_clear()


def _category(value: str) -> str:
    category = re.sub(r"[^a-z0-9-]+", "-", str(value or "").lower()).strip("-")
    if category not in _ALLOWED_CATEGORIES:
        raise InvalidStorageKey("La categoría de archivo no está permitida.")
    return category


def _safe_original_name(original_name: str) -> str:
    value = str(original_name or "archivo").replace("\\", "/")
    value = Path(value).name
    value = "".join(char for char in value if ord(char) >= 32 and char != "\x7f")
    return value.strip()[:300] or "archivo"


def _safe_filename(original_name: str, prefix: str = "") -> str:
    original = _safe_original_name(original_name)
    extension = Path(original).suffix.lower()[:12]
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(prefix or "archivo")).strip("-")[:80]
    return f"{base or 'archivo'}-{uuid.uuid4().hex[:16]}{extension}"


def _require_storage_write(db) -> None:
    """Bloquea efectos externos antes de que el ORM pueda rechazar el flush.

    Storage usa una credencial server-side que omite RLS. Por eso no basta con
    que ``before_flush`` proteja los metadatos: un miembro de solo lectura no
    debe alcanzar ``put``/``delete`` y dejar un objeto huérfano o borrado.
    """
    if es_lectura(db):
        from .models import PermisoOrganizacionError

        raise PermisoOrganizacionError(
            "Tu rol es de solo lectura y no permite modificar archivos."
        )


def save_object(
    db,
    data: bytes,
    category: str,
    original_name: str,
    content_type: str = "",
    prefix: str = "",
    exact_filename: str = "",
    metadata: dict[str, Any] | None = None,
) -> StoredObject:
    """Guarda bytes y registra clave/metadatos dentro de la organización."""
    from .models import ArchivoAlmacenado

    organization_id = int(db.info.get("organizacion_id") or 0)
    if organization_id <= 0:
        raise StorageError("No hay una organización activa para guardar el archivo.")
    _require_storage_write(db)
    if not data or len(data) > MAX_OBJECT_SIZE:
        raise StorageError("El archivo está vacío o supera 12 MB.")
    original_name = _safe_original_name(original_name)
    category = _category(category)
    if exact_filename:
        filename = Path(exact_filename).name
        if filename != exact_filename or not re.fullmatch(r"[A-Za-z0-9_.-]{1,180}", filename):
            raise InvalidStorageKey("El nombre exacto del objeto no es válido.")
    else:
        filename = _safe_filename(original_name, prefix)
    key = validate_tenant_object_key(
        f"organizaciones/{organization_id}/{category}/{filename}", organization_id
    )
    content_type = (
        str(content_type or "").split(";", 1)[0].strip().lower()
        or mimetypes.guess_type(original_name)[0]
        or "application/octet-stream"
    )[:150]
    try:
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise StorageError("Los metadatos del archivo no son JSON válidos.") from exc
    if len(metadata_json.encode("utf-8")) > 16 * 1024:
        raise StorageError("Los metadatos del archivo superan 16 KB.")
    backend = get_storage_backend()
    backend.put(key, data, content_type)
    digest = hashlib.sha256(data).hexdigest()
    stored = StoredObject(
        reference=storage_reference(key), object_key=key,
        backend=backend.name, bucket=backend.bucket,
        content_type=content_type, size=len(data), sha256=digest,
    )
    db.add(ArchivoAlmacenado(
        object_key=key,
        categoria=category,
        nombre_original=original_name,
        content_type=content_type,
        tamano_bytes=len(data),
        sha256=digest,
        metadata_json=metadata_json,
    ))
    return stored


def read_reference(reference: str) -> bytes:
    key = object_key_from_reference(reference)
    if key is not None:
        return get_storage_backend().read(key)
    clean = str(reference or "").strip().lstrip("/")
    if clean.startswith("static/"):
        clean = clean[7:]
    if clean.startswith("uploads/"):
        clean = clean[8:]
    path = (UPLOADS_DIR / clean).resolve()
    root = UPLOADS_DIR.resolve()
    if not clean or root not in path.parents or not path.is_file():
        raise StorageError("El archivo solicitado no existe.")
    if path.stat().st_size > MAX_OBJECT_SIZE:
        raise StorageError("El objeto supera el tamaño permitido.")
    return path.read_bytes()


def delete_object(db, reference: str) -> None:
    from .models import ArchivoAlmacenado

    _require_storage_write(db)
    key = object_key_from_reference(reference)
    if key is None:
        clean = str(reference or "").strip().lstrip("/")
        if clean.startswith("static/"):
            clean = clean[7:]
        if clean.startswith("uploads/"):
            clean = clean[8:]
        try:
            path = (UPLOADS_DIR / clean).resolve()
            if clean and UPLOADS_DIR.resolve() in path.parents:
                path.unlink(missing_ok=True)
        except OSError:
            pass
        return
    metadata = db.query(ArchivoAlmacenado).filter(ArchivoAlmacenado.object_key == key).first()
    if metadata is None:
        return
    get_storage_backend().delete(key)
    db.delete(metadata)


def copy_object(db, reference: str, category: str, prefix: str) -> str:
    from .models import ArchivoAlmacenado

    key = object_key_from_reference(reference)
    metadata = None
    if key is not None:
        metadata = db.query(ArchivoAlmacenado).filter(ArchivoAlmacenado.object_key == key).first()
        if metadata is None:
            return ""
    data = read_reference(reference)
    original = metadata.nombre_original if metadata is not None else Path(reference).name
    content_type = metadata.content_type if metadata is not None else (
        mimetypes.guess_type(original)[0] or "application/octet-stream"
    )
    return save_object(db, data, category, original, content_type, prefix=prefix).reference


def materialize_reference(reference: str) -> Path:
    """Entrega una ruta local para ReportLab/Pillow, usando /tmp como caché."""
    key = object_key_from_reference(reference)
    if key is None:
        clean = str(reference or "").strip().lstrip("/")
        if clean.startswith("static/"):
            clean = clean[7:]
        if clean.startswith("uploads/"):
            return UPLOADS_DIR / clean[8:]
        path = UPLOADS_DIR / clean
        if path.exists():
            return path
        return Path("/__cotizat_archivo_inexistente__")
    backend = get_storage_backend()
    local = backend.local_path(key)
    if local is not None:
        return local
    extension = Path(key).suffix.lower()[:12]
    cache = Path(tempfile.gettempdir()) / "cotizat-storage-cache"
    if cache.is_symlink():
        raise StorageError("La caché temporal de archivos no es segura.")
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(cache, 0o700)
    except OSError:
        pass
    target = cache / (hashlib.sha256(key.encode()).hexdigest() + extension)
    if target.is_symlink():
        raise StorageError("El archivo temporal no es seguro.")
    if not target.is_file():
        data = backend.read(key)
        temporary = target.with_name(target.name + ".tmp-" + uuid.uuid4().hex[:8])
        try:
            temporary.write_bytes(data)
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return target
