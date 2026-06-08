# -*- coding: utf-8 -*-
import os
import ssl
from pathlib import Path


CERT_CACHE_DIR = Path(".tarca_cache")
WINDOWS_CERT_BUNDLE = CERT_CACHE_DIR / "windows_system_roots.pem"


def _env_bool(nombre, default=False):
    valor = os.getenv(nombre)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "t", "yes", "y", "si", "s"}


def _env_int(nombre, default):
    valor = os.getenv(nombre)
    if not valor:
        return default
    try:
        return int(valor)
    except ValueError:
        return default


def _certifi_bundle():
    try:
        import certifi

        return certifi.where()
    except ImportError:
        return None


def _generar_bundle_windows():
    if not hasattr(ssl, "enum_certificates"):
        return None

    CERT_CACHE_DIR.mkdir(exist_ok=True)
    pem_blocks = []

    certifi_path = _certifi_bundle()
    if certifi_path and Path(certifi_path).exists():
        pem_blocks.append(Path(certifi_path).read_text(encoding="ascii", errors="ignore"))

    for store_name in ("ROOT", "CA"):
        try:
            certificados = ssl.enum_certificates(store_name)
        except Exception:
            continue

        for cert_bytes, encoding, _trust in certificados:
            if encoding != "x509_asn":
                continue
            try:
                pem_blocks.append(ssl.DER_cert_to_PEM_cert(cert_bytes))
            except Exception:
                continue

    if not pem_blocks:
        return None

    WINDOWS_CERT_BUNDLE.write_text("\n".join(pem_blocks), encoding="ascii")
    return str(WINDOWS_CERT_BUNDLE.resolve())


def bundle_certificados_google():
    ca_bundle = os.getenv("GEMINI_CA_BUNDLE")
    if ca_bundle:
        return ca_bundle

    if _env_bool("GEMINI_USE_SYSTEM_CERTS", True):
        windows_bundle = _generar_bundle_windows()
        if windows_bundle:
            return windows_bundle

    return _certifi_bundle()


def configurar_certificados_google():
    bundle = bundle_certificados_google()
    if not bundle:
        return None

    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = bundle
    os.environ.setdefault("SSL_CERT_FILE", bundle)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)
    return bundle


def opciones_http_gemini():
    if not _env_bool("GEMINI_SSL_VERIFY", True):
        verify = False
    else:
        verify = configurar_certificados_google()

    client_args = {
        "trust_env": _env_bool("GEMINI_TRUST_ENV", False),
    }
    if verify is not None:
        client_args["verify"] = verify

    return {
        "timeout": _env_int("GEMINI_TIMEOUT_SECONDS", 20) * 1000,
        "clientArgs": client_args,
        "asyncClientArgs": dict(client_args),
    }
