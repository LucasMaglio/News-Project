# Briefing diário — mercado e tecnologia

Página que reúne, todas as manhãs, as notícias de mercado financeiro, tecnologia,
desenvolvimento e segurança, junto com a agenda dos próximos eventos e onde assisti-los.

A coleta roda sozinha no GitHub Actions, sem servidor e sem custo.

## Como funciona

```
09:00 (BRT)   GitHub Actions acorda
              └─ roda coletar.py
                 └─ lê os feeds RSS das fontes configuradas
                    └─ grava dados.json
                       └─ commita no repositório
                          └─ GitHub Pages publica a página nova
```

A página lê dois arquivos:

| Arquivo | Quem mantém | O que tem dentro |
|---|---|---|
| `dados.json` | a automação | as notícias da última coleta |
| `agenda.json` | você, na mão | eventos futuros, onde assistir e o que observar |

Os contadores de dias são calculados no navegador de quem abre a página. Ou seja:
mesmo que a coleta falhe num dia, a agenda continua correta.

## Passo a passo

### 1. Criar o repositório

No GitHub, clique em **New repository**. Nome sugerido: `briefing-diario`.
Marque **Public** (o GitHub Pages gratuito exige repositório público).
Não marque nenhuma das opções de inicialização.

### 2. Subir os arquivos

Pelo site: **uploading an existing file** e arraste tudo, inclusive a pasta `.github`.

Pelo terminal:

```bash
git init
git add .
git commit -m "briefing diário"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/briefing-diario.git
git push -u origin main
```

### 3. Liberar o robô para gravar

**Settings › Actions › General**, seção **Workflow permissions**.
Marque **Read and write permissions** e salve.

Sem isso o robô coleta as notícias mas não consegue publicar.

### 4. Ligar o GitHub Pages

**Settings › Pages**. Em **Source**, escolha **Deploy from a branch**.
Branch `main`, pasta `/ (root)`. Salve.

Em um ou dois minutos o endereço aparece na própria tela:
`https://SEU-USUARIO.github.io/briefing-diario/`

### 5. Rodar a primeira coleta

Aba **Actions › Atualizar briefing › Run workflow**.
Acompanhe o log: ele mostra quantos itens vieram de cada fonte e quais falharam.

### 6. Conferir

Abra o endereço do Pages. O selo no topo deve dizer "Atualizado hoje às ...".
Se disser que a coleta está velha, algo falhou no passo 3 ou 5.

## Manutenção

**Trocar ou incluir uma fonte:** edite a lista `FONTES` no início de `coletar.py`.
Cada item precisa de nome, URL do feed e categoria (`mercado`, `tecnologia`, `dev`
ou `seguranca`).

**Incluir um evento:** edite `agenda.json`. Eventos com data passada somem da página
sozinhos.

**Mudar o horário da coleta:** a linha `cron` em `.github/workflows/atualizar.yml`
usa UTC. `0 12 * * 1-5` equivale a 9h de Brasília, de segunda a sexta.

**Se uma fonte parar de responder:** a página avisa na aba Fontes qual delas falhou.
Feeds mudam de endereço de tempos em tempos; é só atualizar a URL.

## Rodar na sua máquina

```bash
python3 coletar.py     # grava o dados.json
python3 -m http.server # abre em http://localhost:8000
```

Abrir o `index.html` com dois cliques também funciona, mas o navegador bloqueia a
leitura dos arquivos JSON nesse modo. Use o servidor local.

## Sobre as fontes

Este projeto lê apenas feeds RSS públicos e mostra título, resumo curto e link para
a matéria original. O conteúdo pertence a cada veículo.
