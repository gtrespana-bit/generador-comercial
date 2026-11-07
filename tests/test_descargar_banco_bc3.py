"""Descarga y validación del archivo BC3 de una base oficial."""
import pytest

from tools import descargar_banco_bc3 as descarga


def test_valida_un_bc3_minimo(tmp_path):
    ruta = tmp_path / "x.bc3"
    ruta.write_bytes(b"~V|RIB Spain|FIEBDC-3/2020|24042026|Presto\r\n"
                     b"~C|P01DW010|m3|Agua|0.91|240426|0|\r\n")
    assert len(descarga.comprobar_bc3(ruta)) == 64


def test_rechaza_archivos_que_no_son_bc3(tmp_path):
    ruta = tmp_path / "x.bc3"
    ruta.write_bytes(b"<html>no soy una base</html>")
    with pytest.raises(ValueError, match="FIEBDC-3"):
        descarga.comprobar_bc3(ruta)
    ruta.write_bytes(b"~V|RIB|FIEBDC-3/2020|24042026|Presto\r\n")
    with pytest.raises(ValueError, match="~C"):
        descarga.comprobar_bc3(ruta)


def test_la_url_por_defecto_es_la_de_extremadura_2026():
    assert "juntaex.es" in descarga.EXTREMADURA_2026
    assert "BCEXTGREM_26" in descarga.EXTREMADURA_2026
    assert descarga.DESTINO.name == "BCEXTGREM_26_v1.bc3"


def test_si_el_archivo_existe_no_se_descarga(tmp_path, monkeypatch):
    destino = tmp_path / "guardado.bc3"
    destino.write_bytes(b"~V|RIB|FIEBDC-3/2020|24042026|Presto\r\n~C|P1|m3|Agua|1|240426|0|\r\n")
    def falla(*_a, **_k):
        raise AssertionError("no debía descargar")
    monkeypatch.setattr(descarga, "descargar", falla)
    monkeypatch.setattr(descarga, "DESTINO", destino)
    monkeypatch.setattr("sys.argv", ["x", "--destino", str(destino)])
    assert descarga.main() == 0
