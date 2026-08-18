"""Audita el repositorio en busca de datos reales sensibles (E1-021).

Motivación
----------
El repositorio es privado, pero «privado» no es una garantía: basta un fork, un
colaborador nuevo o el día en que se decida abrirlo para que todo lo confirmado
quede expuesto. Esta herramienta convierte la revisión manual de E1-021 en una
comprobación repetible que se ejecuta en cada cambio (la usa
``tests/test_datos_sensibles.py``, y CI ejecuta la suite).

Qué busca
---------
1. **Credenciales**: claves de Supabase (``sb_secret_``/``sb_publishable_``),
   API keys de Resend, JWT de tres partes, tokens de GitHub, claves de AWS,
   tokens de Upstash y bloques PEM de clave privada.
2. **Cadenas de conexión con contraseña real** (``postgresql://usuario:clave@``)
   que no usen un marcador evidente.
3. **Identificadores personales reales**: correos de proveedores de consumo
   (Gmail, Hotmail, Outlook, Yahoo, iCloud, ProtonMail), teléfonos venezolanos o
   españoles y documentos de identidad (RIF/NIF/CIF) que no sean marcadores.
4. **Identificadores de infraestructura propia**: la referencia del proyecto
   Supabase y el subdominio de la base Upstash. No son secretos por sí mismos,
   pero reducen el trabajo de quien quiera atacar la instalación real, así que
   se documentan con marcadores.
5. **Archivos que nunca deben versionarse**: ``.env``, bases de datos, copias de
   seguridad, volcados y material criptográfico.

Qué NO busca
------------
La procedencia y los derechos del catálogo comercial (partidas, descompuestos y
capturas de terceros) son objeto de **E1-022**, no de esta auditoría.

Uso
---
    python tools/auditar_datos_sensibles.py          # informe legible
    python tools/auditar_datos_sensibles.py --json   # salida para máquinas

Devuelve 0 si no hay hallazgos y 1 si encuentra alguno.

Cómo añadir una excepción
-------------------------
Si un hallazgo es legítimo (por ejemplo, un dato ficticio que casualmente
coincide con un patrón), añádelo a ``EXCEPCIONES`` con su motivo escrito. Nunca
se silencia un patrón entero: se silencia una coincidencia concreta.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Iterator, Pattern

REPO = Path(__file__).resolve().parents[1]

# Extensiones que se leen como texto. El resto (fuentes, imágenes, PDF, Excel)
# se comprueba por nombre de archivo, no por contenido.
EXTENSIONES_TEXTO = {
    ".py", ".md", ".txt", ".html", ".js", ".css", ".json", ".yml", ".yaml",
    ".ini", ".cfg", ".toml", ".sql", ".sh", ".bat", ".command", ".spec",
    ".iss", ".mako", ".example", ".lock", ".gitignore", "",
}

# ---------------------------------------------------------------------------
# Reglas
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Regla:
    """Un patrón con nombre y una explicación de por qué importa."""

    nombre: str
    patron: Pattern[str]
    motivo: str


def _r(nombre: str, patron: str, motivo: str) -> Regla:
    return Regla(nombre, re.compile(patron), motivo)


# Palabras que delatan un marcador y no un valor real. Se comprueban sin
# distinguir mayúsculas ni acentos ausentes.
MARCADORES = (
    "reemplazar", "placeholder", "ejemplo", "example", "prueba", "no-real",
    "no_real", "ficticio", "tu-", "tu_", "tucontrasena", "tu contraseña",
    "contraseña", "clave", "secreto", "secret", "xxx", "...", "…", "<", ">",
    "cambiar", "aqui", "aquí", "valor-real", "no-es", "no_debe", "no debe",
)


# Prefijos que forman parte del propio formato de la credencial. Se recortan
# antes de buscar marcadores: de lo contrario `sb_secret_…` contendría siempre
# la palabra «secret» y toda clave de Supabase parecería un marcador.
PREFIJOS_DE_FORMATO = (
    "sb_secret_", "sb_publishable_", "re_", "ghp_", "gho_", "ghu_", "ghs_",
    "ghr_", "github_pat_", "akia", "asia",
)


def _es_marcador(texto: str) -> bool:
    minuscula = texto.lower()
    for prefijo in PREFIJOS_DE_FORMATO:
        if minuscula.startswith(prefijo):
            minuscula = minuscula[len(prefijo) :]
            break
    return any(marcador in minuscula for marcador in MARCADORES)


# Secuencias que delatan un número inventado en teléfonos y documentos: la
# parte identificativa es toda ceros o una cuenta corrida.
SECUENCIAS_EVIDENTES = ("0123456789", "1234567890", "9876543210")


def _es_numero_marcador(texto: str) -> bool:
    """Un teléfono o documento sin dígitos significativos no identifica a nadie.

    Cubre los tres casos que usa el proyecto en marcadores y datos ficticios:
    ``+58 412 000 0000`` (abonado a ceros), ``J-00000000-0`` (RIF marcador) y
    ``J-12345678-9`` (cuenta corrida del formulario de clientes).
    """
    digitos = re.sub(r"\D", "", texto)
    if not digitos:
        return True
    # Cola de ceros: cualquier número con seis o más ceros seguidos.
    if "000000" in digitos:
        return True
    # Cuenta corrida ascendente o descendente de al menos ocho dígitos.
    return any(
        digitos[i : i + 8] in secuencia
        for secuencia in SECUENCIAS_EVIDENTES
        for i in range(max(len(digitos) - 7, 1))
        if len(digitos[i : i + 8]) == 8
    )


REGLAS_CREDENCIALES = (
    _r(
        "clave-secreta-supabase",
        r"sb_secret_[A-Za-z0-9]{20,}",
        "clave de servicio de Supabase: omite RLS y da acceso total al proyecto",
    ),
    _r(
        "clave-publicable-supabase",
        r"sb_publishable_[A-Za-z0-9]{20,}",
        "clave publicable real de Supabase: identifica el proyecto en uso",
    ),
    _r(
        "api-key-resend",
        r"\bre_[A-Za-z0-9]{24,}\b",
        "API key de Resend: permite enviar correo firmado con el dominio propio",
    ),
    _r(
        "jwt",
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        "JWT completo: puede ser un service_role o una sesión de un usuario real",
    ),
    _r(
        "token-github",
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b",
        "token de GitHub: acceso al propio repositorio",
    ),
    _r(
        "clave-aws",
        r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
        "identificador de clave de AWS",
    ),
    _r(
        "clave-privada-pem",
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----",
        "material criptográfico privado",
    ),
    _r(
        "token-upstash",
        r"\bA[A-Za-z0-9_-]{20,}=\s*$",
        "token REST de Upstash (base64 largo terminado en '=')",
    ),
)

# Reglas cuyo hallazgo es un número: se descartan si no tienen dígitos
# significativos (ver ``_es_numero_marcador``).
_REGLAS_NUMERICAS = frozenset(
    {"telefono-venezolano", "telefono-espanol", "documento-fiscal"}
)

# Longitud mínima de una firma JWT real. HS256 firma con 32 bytes, que en
# base64url ocupan 43 caracteres; RS256 produce firmas mucho más largas. Una
# firma más corta es un token de laboratorio, no una credencial que revocar.
LONGITUD_MINIMA_FIRMA_JWT = 43


def _es_jwt_de_prueba(texto: str) -> bool:
    """Distingue un JWT inventado en las pruebas de una credencial real."""
    partes = texto.split(".")
    if len(partes) != 3:
        return True
    return len(partes[2]) < LONGITUD_MINIMA_FIRMA_JWT


REGLAS_CONEXION = (
    _r(
        "cadena-de-conexion-con-contrasena",
        r"postgres(?:ql)?://[A-Za-z0-9_.+-]+:([^@\s'\"<>]{4,})@[A-Za-z0-9.-]+",
        "cadena de conexión con contraseña incrustada",
    ),
)

# Proveedores de correo de consumo: si aparece uno, es la dirección real de una
# persona, no un ejemplo. Los ejemplos deben usar example.com / ejemplo.com /
# dominios .test o .invalid (RFC 2606 y RFC 6761).
DOMINIOS_PERSONALES = (
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.es", "outlook.com",
    "outlook.es", "live.com", "yahoo.com", "yahoo.es", "icloud.com", "me.com",
    "protonmail.com", "proton.me", "aol.com", "yandex.com", "gmx.com",
)

REGLAS_PERSONALES = (
    _r(
        "correo-personal",
        r"[A-Za-z0-9._%+-]+@(?:" + "|".join(d.replace(".", r"\.") for d in DOMINIOS_PERSONALES) + r")\b",
        "dirección de correo de una persona real",
    ),
    _r(
        "telefono-venezolano",
        r"(?:\+58[\s.-]?|\b0)(?:2\d{2}|4(?:12|14|16|24|26))[\s.-]?\d{3}[\s.-]?\d{4}\b",
        "número de teléfono venezolano real",
    ),
    _r(
        "telefono-espanol",
        r"(?:\+34[\s.-]?)(?:6|7|8|9)\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b",
        "número de teléfono español real",
    ),
    _r(
        "documento-fiscal",
        r"\b[JGVEP]-?\d{8}-?\d\b",
        "documento fiscal (RIF/NIF) que podría corresponder a una empresa real",
    ),
)

REGLAS_INFRAESTRUCTURA = (
    _r(
        "referencia-proyecto-supabase",
        r"\b[a-z]{20}\.supabase\.(?:co|in)\b|\b(?:postgres|cotizat_runtime)\.[a-z]{20}\b",
        "referencia del proyecto Supabase real (identifica la instalación)",
    ),
    _r(
        "base-upstash",
        r"\bhttps://(?!tu-|mi-)[a-z0-9-]+-\d{4,}\.upstash\.io\b",
        "URL de la base Upstash real",
    ),
)

TODAS_LAS_REGLAS = (
    REGLAS_CREDENCIALES
    + REGLAS_CONEXION
    + REGLAS_PERSONALES
    + REGLAS_INFRAESTRUCTURA
)

# Archivos que nunca deben estar versionados, comprobados por nombre.
PATRONES_DE_ARCHIVO_PROHIBIDO = (
    # `.env.example` es la plantilla documentada y solo contiene marcadores.
    (re.compile(r"(^|/)\.env(?!\.example$)(\..+)?$"), "variables de entorno reales"),
    (re.compile(r"\.(db|sqlite|sqlite3)$"), "base de datos con datos de trabajo"),
    (re.compile(r"\.(pem|key|p12|pfx|jks|keystore)$"), "material criptográfico"),
    (re.compile(r"\.(dump|bak)$"), "volcado o copia de seguridad"),
    (re.compile(r"(^|/)(backups|private_storage)/"), "copias o almacenamiento privado"),
    (re.compile(r"(^|/)app/static/uploads/"), "archivos subidos por usuarios"),
    (re.compile(r"(^|/)\.vercel/"), "credenciales del proyecto Vercel"),
    (re.compile(r"(^|/)\.netrc$|(^|/)\.git-credentials$"), "credenciales guardadas"),
)

# Rutas que la auditoría no inspecciona por contenido: contienen los propios
# patrones como parte de su definición.
ARCHIVOS_DE_LA_AUDITORIA = (
    "tools/auditar_datos_sensibles.py",
    "tests/test_datos_sensibles.py",
)

# Excepciones exactas: (ruta, nombre de regla, texto encontrado) -> motivo.
# Cada una debe explicar por qué el hallazgo es legítimo.
EXCEPCIONES: dict[tuple[str, str, str], str] = {
    (
        "app/services/presupuesto_muestra.py",
        "documento-fiscal",
        "J-00000000-0",
    ): "RIF marcador (todo ceros) del presupuesto de ejemplo; no existe.",
    (
        "tests/test_presupuesto_muestra.py",
        "documento-fiscal",
        "J-00000000-0",
    ): "El test comprueba justamente que el PDF de ejemplo use el RIF marcador.",
    (
        "docs/MATRIZ_PASOS_MANUALES.md",
        "correo-personal",
        "tucorreo+b@gmail.com",
    ): "Instrucción genérica sobre el truco de subdirecciones de Gmail; "
       "'tucorreo' es un marcador, no una cuenta.",
    (
        "app/datos_pago.py",
        "telefono-venezolano",
        "0412-6443099",
    ): "Canal de Pago móvil del titular, publicado deliberadamente en la "
       "página de pago (E1-059 cobro manual).",
    (
        "app/datos_pago.py",
        "telefono-venezolano",
        "+58412-3215016",
    ): "Canal de Kontigo del titular, publicado deliberadamente en la página "
       "de pago (E1-059 cobro manual).",
}


@dataclass(frozen=True)
class Hallazgo:
    ruta: str
    linea: int
    regla: str
    motivo: str
    extracto: str

    def __str__(self) -> str:  # pragma: no cover - formato de informe
        return f"{self.ruta}:{self.linea}: [{self.regla}] {self.extracto} — {self.motivo}"


def archivos_versionados(repo: Path = REPO) -> list[str]:
    """Devuelve las rutas versionadas en Git (lo que se publicaría al abrir el repo)."""
    salida = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [ruta for ruta in salida.split("\0") if ruta]


def _es_texto(ruta: str) -> bool:
    sufijo = Path(ruta).suffix.lower()
    if sufijo in EXTENSIONES_TEXTO:
        return True
    return Path(ruta).name in {"README", "Makefile", "Dockerfile"}


def _redactar(texto: str, maximo: int = 60) -> str:
    """Recorta el extracto para no reproducir un secreto completo en el informe."""
    texto = texto.strip()
    if len(texto) <= maximo:
        return texto
    return texto[:maximo] + "…"


def _hallazgos_de_contenido(ruta: str, contenido: str) -> Iterator[Hallazgo]:
    for numero, linea in enumerate(contenido.splitlines(), start=1):
        for regla in TODAS_LAS_REGLAS:
            for coincidencia in regla.patron.finditer(linea):
                texto = coincidencia.group(0)
                if regla.nombre == "cadena-de-conexion-con-contrasena":
                    # Solo importa si la contraseña no es un marcador.
                    if _es_marcador(coincidencia.group(1)):
                        continue
                elif regla.nombre == "jwt" and _es_jwt_de_prueba(texto):
                    continue
                elif regla in REGLAS_CREDENCIALES and _es_marcador(texto):
                    continue
                elif regla.nombre in _REGLAS_NUMERICAS and _es_numero_marcador(texto):
                    continue
                if EXCEPCIONES.get((ruta, regla.nombre, texto)):
                    continue
                yield Hallazgo(ruta, numero, regla.nombre, regla.motivo, _redactar(texto))


def auditar(repo: Path = REPO, rutas: Iterable[str] | None = None) -> list[Hallazgo]:
    """Ejecuta la auditoría completa y devuelve la lista de hallazgos."""
    hallazgos: list[Hallazgo] = []
    for ruta in rutas if rutas is not None else archivos_versionados(repo):
        for patron, motivo in PATRONES_DE_ARCHIVO_PROHIBIDO:
            if patron.search(ruta):
                hallazgos.append(
                    Hallazgo(ruta, 0, "archivo-prohibido", motivo, Path(ruta).name)
                )
        if ruta in ARCHIVOS_DE_LA_AUDITORIA or not _es_texto(ruta):
            continue
        destino = repo / ruta
        if not destino.is_file():
            continue
        try:
            contenido = destino.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hallazgos.extend(_hallazgos_de_contenido(ruta, contenido))
    return hallazgos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="salida en JSON")
    args = parser.parse_args(argv)

    hallazgos = auditar()

    if args.json:
        print(json.dumps([asdict(h) for h in hallazgos], ensure_ascii=False, indent=2))
    elif hallazgos:
        print(f"Se encontraron {len(hallazgos)} posibles datos sensibles:\n")
        for hallazgo in hallazgos:
            print(f"  {hallazgo}")
        print(
            "\nCorrige el dato o, si es legítimo, añádelo a EXCEPCIONES en "
            "tools/auditar_datos_sensibles.py explicando por qué."
        )
    else:
        total = len(archivos_versionados())
        print(f"Sin hallazgos: {total} archivos versionados revisados (E1-021).")

    return 1 if hallazgos else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
