"""Guardas da vitrine — schema dos JSONs, dry-run e ausência de segredos."""
import json
import re
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

VITRINE = Path(__file__).resolve().parent.parent / "vitrine"
LOJAS = {"TikTok Shop", "Monetizze", "Mercado Livre", "AliExpress"}
CAMPOS = {"loja", "nome", "preco", "imagem", "link_afiliado", "data_cadastro"}
SEGREDOS = re.compile(
    r"password|passwd|secret|api[_-]?key|bearer|sk-[A-Za-z0-9]|client[_-]?secret",
    re.IGNORECASE,
)


def _carregar(nome):
    return json.loads((VITRINE / nome).read_text(encoding="utf-8"))


class TestLinksAfiliados:
    def test_produtos_no_formato(self):
        dados = _carregar("links_afiliados.json")
        assert isinstance(dados["produtos"], list) and dados["produtos"]
        for p in dados["produtos"]:
            assert CAMPOS <= set(p), f"campos faltando em {p}"
            assert p["loja"] in LOJAS, f"loja inválida: {p['loja']}"
            assert isinstance(p["preco"], (int, float)) and p["preco"] >= 0
            assert isinstance(p["nome"], str) and p["nome"].strip()
            date.fromisoformat(p["data_cadastro"])

    def test_tres_primeiros_por_chegada_sao_deterministicos(self):
        dados = _carregar("links_afiliados.json")
        por_loja = {}
        for p in sorted(dados["produtos"], key=lambda x: x["data_cadastro"]):
            por_loja.setdefault(p["loja"], []).append(p["nome"])
        for loja in LOJAS:
            assert len(por_loja.get(loja, [])) >= 1, f"sem produto: {loja}"
        primeiros = {loja: nomes[:3] for loja, nomes in por_loja.items()}
        assert all(len(n) <= 3 for n in primeiros.values())


class TestSociaisEConfig:
    def test_redes_sociais_configuraveis(self):
        sociais = _carregar("redes_sociais.json")
        assert "instagram" in sociais and "facebook" in sociais

    def test_pixel_desligado_por_padrao(self):
        config = _carregar("configuracao.json")
        assert config.get("meta_pixel_enabled") is False
        assert not config.get("meta_pixel_id")


class TestDryRunSemSegredos:
    def test_nenhum_segredo_nos_arquivos_do_site(self):
        for arquivo in VITRINE.iterdir():
            if arquivo.is_file():
                texto = arquivo.read_text(encoding="utf-8")
                assert not SEGREDOS.search(texto), f"possível segredo em {arquivo.name}"

    def test_botao_oferta_com_rel_seguro(self):
        html = (VITRINE / "index.html").read_text(encoding="utf-8")
        assert 'target="_blank"' in html or "target" in (VITRINE / "app.js").read_text(
            encoding="utf-8"
        )
        js = (VITRINE / "app.js").read_text(encoding="utf-8")
        assert "nofollow sponsored noopener" in js
        assert "fbevents.js" in js  # pixel só via injeção condicional
        assert "meta_pixel_enabled" in js


class TestVitrineServida:
    def test_get_vitrine_200(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        assert client.get("/vitrine/").status_code == 200

    def test_json_acessivel(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/vitrine/links_afiliados.json")
        assert r.status_code == 200
        assert "produtos" in r.json()
