#!/usr/bin/env python3
"""
Gera o site estático a partir do conteúdo em content/.

Estrutura esperada:
  content/
    2026-1/                          <- pasta do semestre (qualquer nome, ex: 2026-1)
      _semestre.yaml (opcional)      <- {titulo: "2026.1"}
      calculo-1/                     <- pasta da disciplina
        _disciplina.yaml             <- {titulo, descricao, professor}
        01-introducao/               <- pasta da aula
          _aula.yaml                 <- {titulo, data, resumo, materiais: [...]}
          slides-aula-01.pdf         <- qualquer arquivo referenciado em materiais
          lista-01.pdf

Rode: python scripts/build.py
Saída: pasta docs/ (pronta para publicar no GitHub Pages)
"""
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUT_DIR = ROOT / "docs"

# descricao dos blocos de avaliacao (P1/P2/P3) mostrada nos cards da pagina da disciplina
BLOCOS_META = {
    1: {
        "titulo": "Bloco 1 — Prova P1",
        "descricao": "Estatística descritiva, probabilidade e variáveis aleatórias.",
    },
    2: {
        "titulo": "Bloco 2 — Prova P2",
        "descricao": "Modelos de distribuição discretos e contínuos, aproximação normal e distribuições amostrais.",
    },
    3: {
        "titulo": "Bloco 3 — Prova P3",
        "descricao": "Intervalos de confiança, testes de hipótese e regressão linear.",
    },
}


def slugify(name: str) -> str:
    return name


def load_yaml(path: Path, default=None):
    if not path.exists():
        return default or {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def encontrar_arquivos(node):
    """Percorre a estrutura da aula (dicts/listas aninhados) e coleta todo valor
    de uma chave que contenha 'arquivo' (arquivo, arquivo_pdf, etc.), em qualquer
    secao (slides, exercicios, tarefa_complementar, etc.)."""
    achados = []
    if isinstance(node, dict):
        for k, v in node.items():
            if "arquivo" in k and isinstance(v, str):
                achados.append(v)
        for v in node.values():
            achados.extend(encontrar_arquivos(v))
    elif isinstance(node, list):
        for item in node:
            achados.extend(encontrar_arquivos(item))
    return achados


def build():
    if not CONTENT_DIR.exists():
        print(f"ERRO: pasta de conteúdo não encontrada: {CONTENT_DIR}")
        sys.exit(1)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    semestres = []
    for semestre_dir in sorted(CONTENT_DIR.iterdir()):
        if not semestre_dir.is_dir() or semestre_dir.name.startswith("."):
            continue
        semestre_meta = load_yaml(semestre_dir / "_semestre.yaml")
        semestre = {
            "slug": slugify(semestre_dir.name),
            "titulo": semestre_meta.get("titulo", semestre_dir.name),
            "disciplinas": [],
        }

        for disciplina_dir in sorted(semestre_dir.iterdir()):
            if not disciplina_dir.is_dir() or disciplina_dir.name.startswith("."):
                continue
            disc_meta = load_yaml(disciplina_dir / "_disciplina.yaml")
            disciplina = {
                "slug": slugify(disciplina_dir.name),
                "titulo": disc_meta.get("titulo", disciplina_dir.name),
                "descricao": disc_meta.get("descricao", ""),
                "professor": disc_meta.get("professor", ""),
                "aulas": [],
            }

            for aula_dir in sorted(disciplina_dir.iterdir()):
                if not aula_dir.is_dir() or aula_dir.name.startswith("."):
                    continue
                aula_meta = load_yaml(aula_dir / "_aula.yaml")
                if not aula_meta:
                    continue
                aula = dict(aula_meta)
                aula["slug"] = slugify(aula_dir.name)
                aula.setdefault("titulo", aula_dir.name)
                aula.setdefault("data", "")
                aula.setdefault("resumo", "")
                aula["_src_dir"] = aula_dir
                disciplina["aulas"].append(aula)

            disciplina["aulas"].sort(key=lambda a: (a["data"], a["slug"]))

            blocos_dict = {}
            for aula in disciplina["aulas"]:
                blocos_dict.setdefault(aula.get("bloco", 0), []).append(aula)
            blocos = []
            for num in sorted(blocos_dict):
                meta = BLOCOS_META.get(num, {"titulo": f"Bloco {num}", "descricao": ""})
                blocos.append(
                    {
                        "numero": num,
                        "slug": f"bloco-{num}",
                        "titulo": meta["titulo"],
                        "descricao": meta["descricao"],
                        "aulas": blocos_dict[num],
                    }
                )
            disciplina["blocos"] = blocos

            semestre["disciplinas"].append(disciplina)

        semestre["disciplinas"].sort(key=lambda d: d["titulo"])
        semestres.append(semestre)

    semestres.sort(key=lambda s: s["slug"], reverse=True)

    # limpa saída
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # copia estáticos
    shutil.copytree(STATIC_DIR, OUT_DIR / "static")

    # index geral
    tpl = env.get_template("index.html")
    (OUT_DIR / "index.html").write_text(
        tpl.render(root="", semestres=semestres), encoding="utf-8"
    )

    for semestre in semestres:
        sem_dir = OUT_DIR / semestre["slug"]
        sem_dir.mkdir(parents=True, exist_ok=True)
        tpl = env.get_template("semestre.html")
        (sem_dir / "index.html").write_text(
            tpl.render(root="../", semestre=semestre), encoding="utf-8"
        )

        for disciplina in semestre["disciplinas"]:
            disc_dir = sem_dir / disciplina["slug"]
            disc_dir.mkdir(parents=True, exist_ok=True)
            tpl = env.get_template("disciplina.html")
            (disc_dir / "index.html").write_text(
                tpl.render(root="../../", semestre=semestre, disciplina=disciplina),
                encoding="utf-8",
            )

            # pagina de cada bloco (P1/P2/P3) - pasta irma das pastas de aula dentro
            # da disciplina, assim as urls das aulas (e os links do Colab, que ja
            # apontam pra elas) continuam exatamente as mesmas
            for bloco in disciplina["blocos"]:
                bloco_dir = disc_dir / bloco["slug"]
                bloco_dir.mkdir(parents=True, exist_ok=True)
                tpl = env.get_template("bloco.html")
                (bloco_dir / "index.html").write_text(
                    tpl.render(
                        root="../../../",
                        semestre=semestre,
                        disciplina=disciplina,
                        bloco=bloco,
                    ),
                    encoding="utf-8",
                )

            for aula in disciplina["aulas"]:
                aula_dir = disc_dir / aula["slug"]
                aula_dir.mkdir(parents=True, exist_ok=True)
                tpl = env.get_template("aula.html")
                (aula_dir / "index.html").write_text(
                    tpl.render(
                        root="../../../",
                        semestre=semestre,
                        disciplina=disciplina,
                        aula=aula,
                    ),
                    encoding="utf-8",
                )

                # copia os arquivos referenciados em qualquer secao (slides, exercicios,
                # tarefa complementar, etc.) para a pasta arquivos/ do aula publicado
                arquivos_dir = aula_dir / "arquivos"
                for nome_arquivo in encontrar_arquivos(aula):
                    src = aula["_src_dir"] / nome_arquivo
                    if src.exists():
                        arquivos_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, arquivos_dir / nome_arquivo)
                    else:
                        print(f"  aviso: arquivo não encontrado -> {src}")

    # necessário para o GitHub Pages não tentar processar com Jekyll
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    total_aulas = sum(len(d["aulas"]) for s in semestres for d in s["disciplinas"])
    print(f"Site gerado em {OUT_DIR}")
    print(f"  {len(semestres)} semestre(s), {sum(len(s['disciplinas']) for s in semestres)} disciplina(s), {total_aulas} aula(s)")


if __name__ == "__main__":
    build()
