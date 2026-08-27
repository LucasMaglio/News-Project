# Briefing diário — mercado financeiro e tecnologia

**[Ver a página no ar →](https://lucasmaglio.github.io/News-Project/)**

Página que reúne, toda manhã, as notícias de mercado financeiro, tecnologia,
desenvolvimento e segurança, junto com a agenda dos próximos eventos e onde
assisti-los. A coleta roda sozinha, sem servidor e sem custo.

---

## O problema

Acompanhar o que acontece em mercado e tecnologia significa abrir seis ou sete
sites todo dia e reler o que já se leu ontem. Eu queria uma tela só, que
mostrasse o que é novo e o que está chegando.

## Como funciona

```
09:00 (Brasília)   GitHub Actions acorda
                   |
                   +-- roda coletar.py
                         |
                         +-- lê os feeds RSS das fontes configuradas
                               |
                               +-- filtra as últimas 36h e remove repetidos
                                     |
                                     +-- grava dados.json e commita
                                           |
                                           +-- GitHub Pages publica
```

A página consome dois arquivos:

| Arquivo | Quem mantém | Conteúdo |
|---|---|---|
| `dados.json` | a automação | notícias da última coleta |
| `agenda.json` | eu, à mão | eventos, onde assistir, o que observar |

Os contadores de dias da agenda são calculados no navegador de quem abre a
página. Se a coleta falhar num dia, a agenda continua correta.

## Stack

- **Python 3.12**, só biblioteca padrão — sem `pip install`, sem
  `requirements.txt`, sem dependência para quebrar no futuro
- **HTML, CSS e JavaScript puros** — nenhum framework, nenhum build
- **GitHub Actions** para o agendamento
- **GitHub Pages** para a hospedagem

## Decisões que valem explicar

**Por que RSS e não uma API de notícias.** APIs de notícias cobram por volume e
criam dependência de um fornecedor. RSS é gratuito, é padrão aberto e cada
veículo mantém o seu. O custo é que feeds mudam de endereço às vezes — daí o
tratamento de erro descrito abaixo.

**Por que sem dependência externa.** Um projeto que precisa de `pip install`
quebra quando uma biblioteca muda de versão. Usando só `urllib` e
`xml.etree`, ele roda hoje e daqui a três anos. Custou umas quarenta linhas a
mais no parser de RSS e Atom.

**Por que falha de forma parcial.** Uma fonte fora do ar não derruba a coleta:
ela é registrada em `fontes_com_erro`, aparece no log do Actions e na própria
página. Melhor entregar sete fontes de oito do que nada.

**Por que o commit é condicional.** O workflow só faz push se o `dados.json`
mudou. Isso evita encher o histórico de commits idênticos em dia parado.

## Segurança

Feed é conteúdo de terceiro. Se um veículo tiver o feed comprometido, o que
chega aqui não é confiável. Duas barreiras:

1. **Na coleta** (`coletar.py`): a função `link_seguro()` aceita apenas
   endereços `http://` e `https://`. Item com `javascript:`, `data:` ou
   qualquer outro esquema é descartado antes de entrar no `dados.json`.
2. **Na renderização** (`index.html`): a mesma checagem antes de montar cada
   link, mais escape de HTML em todo texto vindo do feed. Se algo passar da
   primeira camada, o título aparece como texto simples, sem link.

Validar na entrada e de novo na saída é redundante de propósito. As duas
camadas foram escritas em momentos diferentes, e é justamente aí que mora o
erro que uma sozinha deixaria passar.

## Rodar localmente

```bash
python3 coletar.py       # busca os feeds e grava o dados.json
python3 -m http.server   # abre em http://localhost:8000
```

Abrir o `index.html` com dois cliques mostra o layout, mas o navegador bloqueia
a leitura dos JSON via `file://` e as listas ficam vazias. Use o servidor local.

## Estrutura

```
index.html                          página, sem dependência externa
coletar.py                          coletor de RSS/Atom
agenda.json                         eventos futuros
dados.json                          saída da coleta (gerado)
.github/workflows/atualizar.yml     agendamento
```

## Manutenção

- **Trocar fonte:** editar a lista `FONTES`, no início do `coletar.py`
- **Incluir evento:** editar `agenda.json`; eventos passados somem sozinhos
- **Mudar horário:** a linha `cron` do workflow usa UTC (`0 12` = 9h de Brasília)

---

Feito por [Lucas Mascarenhas Maglio](https://www.linkedin.com/in/lucasmaglio102/).
O conteúdo das notícias pertence aos veículos de origem; este projeto exibe
título, resumo curto e link para a matéria original.
