#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Le os feeds RSS/Atom configurados e grava dados.json.

Sem dependencia externa: usa so a biblioteca padrao do Python.
Um feed que falhar nao derruba a execucao - ele e registrado em
"fontes_com_erro" e aparece na propria pagina.
"""

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape

# Fuso de Brasilia (sem horario de verao)
BRT = timezone(timedelta(hours=-3))

# Quantas horas para tras considerar "novidade"
JANELA_HORAS = 36

# Maximo de itens por fonte
MAX_POR_FONTE = 4

# ---------------------------------------------------------------
# Fontes. Para trocar uma fonte, basta editar esta lista.
# Se alguma URL sair do ar, o script avisa em vez de quebrar.
# ---------------------------------------------------------------
FONTES = [
    {"nome": "InfoMoney",      "url": "https://www.infomoney.com.br/feed/",        "categoria": "mercado"},
    {"nome": "Money Times",    "url": "https://www.moneytimes.com.br/feed/",       "categoria": "mercado"},
    {"nome": "Tecnoblog",      "url": "https://tecnoblog.net/feed/",               "categoria": "tecnologia"},
    {"nome": "Canaltech",      "url": "https://canaltech.com.br/rss/",             "categoria": "tecnologia"},
    {"nome": "InfoQ Brasil",   "url": "https://feed.infoq.com/br/",                "categoria": "dev"},
    {"nome": "Spring Blog",    "url": "https://spring.io/blog.atom",               "categoria": "dev"},
    {"nome": "Hacker News",    "url": "https://hnrss.org/frontpage?points=200",    "categoria": "dev"},
    {"nome": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "categoria": "seguranca"},
]

CABECALHOS = {
    "User-Agent": "briefing-diario/1.0 (+github actions; leitor de RSS pessoal)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}


def limpar_html(texto):
    """Tira tags, normaliza espacos e devolve texto puro."""
    if not texto:
        return ""
    texto = re.sub(r"<script.*?</script>", " ", texto, flags=re.S | re.I)
    texto = re.sub(r"<style.*?</style>", " ", texto, flags=re.S | re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def resumir(texto, limite=260):
    texto = limpar_html(texto)
    if len(texto) <= limite:
        return texto
    corte = texto[:limite]
    if " " in corte:
        corte = corte[: corte.rfind(" ")]
    return corte + "..."


def ler_data(valor):
    """Aceita RFC 822 (RSS) e ISO 8601 (Atom). Devolve datetime com fuso ou None."""
    if not valor:
        return None
    valor = valor.strip()
    try:
        d = parsedate_to_datetime(valor)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        pass
    try:
        d = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


ESQUEMAS_ACEITOS = ("http://", "https://")


def link_seguro(url):
    """
    So aceita http e https.

    Feeds sao conteudo de terceiros. Um endereco 'javascript:' ou 'data:'
    vindo de um feed comprometido viraria execucao de codigo na pagina,
    entao esses itens sao descartados ainda na coleta.
    """
    if not url:
        return None
    url = url.strip().replace("\n", "").replace("\r", "").replace("\t", "")
    if url.lower().startswith(ESQUEMAS_ACEITOS):
        return url
    return None


def tag(elemento):
    """Nome da tag sem o namespace."""
    return elemento.tag.split("}")[-1]


def extrair_itens(xml_bruto):
    """Devolve uma lista de dicts a partir de RSS ou Atom."""
    raiz = ET.fromstring(xml_bruto)
    itens = []

    for no in raiz.iter():
        if tag(no) not in ("item", "entry"):
            continue

        titulo = link = descricao = data = ""
        for filho in no:
            nome = tag(filho)
            if nome == "title" and not titulo:
                titulo = (filho.text or "").strip()
            elif nome == "link":
                # RSS guarda no texto; Atom guarda no atributo href
                if filho.get("href"):
                    if filho.get("rel", "alternate") == "alternate" and not link:
                        link = filho.get("href")
                elif (filho.text or "").strip() and not link:
                    link = filho.text.strip()
            elif nome in ("description", "summary", "content", "encoded") and not descricao:
                descricao = "".join(filho.itertext()) if len(filho) else (filho.text or "")
            elif nome in ("pubDate", "published", "updated", "date") and not data:
                data = (filho.text or "").strip()

        link = link_seguro(link)
        if titulo and link:
            itens.append({
                "titulo": limpar_html(titulo),
                "link": link,
                "resumo": resumir(descricao),
                "data": ler_data(data),
            })

    return itens


def buscar(fonte):
    contexto = ssl.create_default_context()
    req = urllib.request.Request(fonte["url"], headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=25, context=contexto) as resp:
        return resp.read()


def coletar():
    agora = datetime.now(BRT)
    corte = agora - timedelta(hours=JANELA_HORAS)

    coletados = []
    erros = []
    vistos = set()

    for fonte in FONTES:
        try:
            bruto = buscar(fonte)
            itens = extrair_itens(bruto)
        except (urllib.error.URLError, urllib.error.HTTPError, ET.ParseError, TimeoutError) as e:
            erros.append({"fonte": fonte["nome"], "motivo": type(e).__name__})
            print("  falhou: %s (%s)" % (fonte["nome"], type(e).__name__), file=sys.stderr)
            continue
        except Exception as e:  # noqa: BLE001 - um feed torto nao pode derrubar o resto
            erros.append({"fonte": fonte["nome"], "motivo": type(e).__name__})
            print("  falhou: %s (%s)" % (fonte["nome"], type(e).__name__), file=sys.stderr)
            continue

        recentes = [i for i in itens if i["data"] is None or i["data"] >= corte]
        recentes.sort(key=lambda i: i["data"] or corte, reverse=True)

        contador = 0
        for item in recentes:
            chave = re.sub(r"[^a-z0-9]", "", item["titulo"].lower())[:60]
            if chave in vistos:
                continue
            vistos.add(chave)

            coletados.append({
                "titulo": item["titulo"],
                "resumo": item["resumo"],
                "link": item["link"],
                "fonte": fonte["nome"],
                "categoria": fonte["categoria"],
                "data": (item["data"].astimezone(BRT).isoformat() if item["data"] else None),
            })
            contador += 1
            if contador >= MAX_POR_FONTE:
                break

        print("  ok: %s (%d itens)" % (fonte["nome"], contador))

    coletados.sort(key=lambda i: i["data"] or "", reverse=True)

    return {
        "gerado_em": agora.isoformat(),
        "janela_horas": JANELA_HORAS,
        "total": len(coletados),
        "itens": coletados,
        "fontes_com_erro": erros,
    }


if __name__ == "__main__":
    print("Coletando feeds...")
    dados = coletar()
    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    print("dados.json gravado: %d itens, %d fonte(s) com erro."
          % (dados["total"], len(dados["fontes_com_erro"])))
