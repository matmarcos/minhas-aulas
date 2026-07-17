# Minhas Aulas — site estático para material de curso

Solução definitiva para parar de recriar a disciplina no Moodle todo semestre.
Você organiza os arquivos em pastas, roda um script, e o site é gerado
automaticamente. Para um novo semestre, é só copiar a estrutura de pastas do
semestre anterior e trocar o conteúdo — nunca mais recriar do zero.

## Como funciona

Todo o conteúdo fica em `content/`, organizado assim:

```
content/
  2026-1/                          <- pasta do semestre
    calculo-1/                     <- pasta da disciplina
      _disciplina.yaml
      01-introducao-a-limites/     <- pasta da aula
        _aula.yaml
        slides-aula-01.pdf
        lista-01.pdf
      02-derivadas/
        _aula.yaml
        slides-aula-02.pdf
```

Cada `_aula.yaml` descreve o que aparece na página daquela aula:

```yaml
titulo: "Aula 01 - Introdução a Limites"
data: "2026-03-02"
resumo: "Definição intuitiva de limite, propriedades básicas e exemplos."
materiais:
  - tipo: slides
    titulo: "Slides da aula 01"
    arquivo: "slides-aula-01.pdf"    # arquivo dentro da própria pasta da aula
  - tipo: video
    titulo: "Gravação da aula"
    url: "https://www.youtube.com/watch?v=EXEMPLO"   # link externo (YouTube, Drive, etc.)
  - tipo: exercicio
    titulo: "Lista de exercícios 01"
    arquivo: "lista-01.pdf"
```

Rodando o script, o site inteiro (HTML, CSS, e cópia dos arquivos) é gerado
dentro da pasta `docs/`, pronta para publicar.

## Gerar o site

```bash
pip install -r requirements.txt
python scripts/build.py
```

Isso recria a pasta `docs/` do zero a cada execução.

Para conferir localmente antes de publicar:

```bash
cd docs && python3 -m http.server 8000
# abra http://localhost:8000 no navegador
```

## Preparar um novo semestre (o problema que você queria resolver)

1. Copie a pasta do semestre anterior, ex: `content/2026-1` → `content/2026-2`.
2. Dentro da cópia, apague as aulas antigas (ou deixe como referência) e vá
   adicionando as aulas novas — cada uma é só uma pasta com `_aula.yaml` e os
   arquivos.
3. Rode `python scripts/build.py`.
4. Publique (`git add`, `git commit`, `git push` — ver abaixo).

Nenhuma disciplina precisa ser "recriada" — a estrutura e o design já
existem, você só adiciona conteúdo.

## Publicar de graça no GitHub Pages

1. Crie uma conta no [GitHub](https://github.com) (gratuita) se ainda não tiver.
2. Crie um repositório novo, por exemplo `minhas-aulas` (pode ser privado).
3. Suba este projeto inteiro para o repositório:
   ```bash
   git init
   git add .
   git commit -m "site inicial"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/minhas-aulas.git
   git push -u origin main
   ```
4. No GitHub, vá em **Settings → Pages**. Em "Build and deployment", escolha
   **Deploy from a branch**, branch `main`, pasta `/docs`. Salve.
5. Em alguns minutos o site estará no ar em
   `https://SEU_USUARIO.github.io/minhas-aulas/`.

Sempre que você rodar `python scripts/build.py` e der `git push` de novo, o
site atualiza sozinho.

## Restringir acesso por turma (login dos alunos)

GitHub Pages sozinho é público — qualquer pessoa com o link acessa. Para
exigir login e liberar só quem está matriculado naquele semestre, sem pagar
nada e sem programar um sistema de login do zero, a forma mais simples é
colocar o site atrás do **Cloudflare Access** (gratuito até 50 usuários,
mais que suficiente para uma turma):

1. Crie uma conta gratuita em [Cloudflare](https://dash.cloudflare.com) e
   ative o **Cloudflare Zero Trust** (tem plano gratuito).
2. Em vez de apontar direto para `SEU_USUARIO.github.io`, use um domínio
   próprio (pode ser um domínio barato, tipo `.com` por ~R$40/ano, ou mesmo
   um subdomínio gratuito de serviços como `.eu.org`) apontando para o
   GitHub Pages, e ative o proxy da Cloudflare para esse domínio.
3. Em **Zero Trust → Access → Applications**, crie uma aplicação apontando
   para o caminho da turma, por exemplo `seusite.com/2026-1/*`.
4. Configure a política de acesso como **"Emails ending in"** com o domínio
   da instituição (ex: `@aluno.suauniversidade.br`), ou **"Emails"** com a
   lista exata dos alunos matriculados naquele semestre.
5. Pronto: quando um aluno acessa o link daquela turma, a Cloudflare pede
   para ele fazer login com o e-mail (recebe um código por e-mail, sem
   precisar de senha) e só libera se o e-mail estiver na lista.

Cada semestre você só troca a lista de e-mails da política — a estrutura do
site continua a mesma.

**Se você não precisar de controle de acesso de verdade** (por exemplo, se
não tem problema em o material ficar público, ou só quer dificultar acesso
casual), pode pular o Cloudflare Access e usar o GitHub Pages puro — daí é
só divulgar o link para a turma.

## Estrutura do projeto

```
content/     conteúdo das aulas (o que você edita a cada semestre)
templates/   layout HTML (Jinja2) — raramente precisa mexer aqui
static/css/  estilo visual do site
scripts/     build.py, o gerador
docs/        saída gerada (é o que vira o site publicado)
```
