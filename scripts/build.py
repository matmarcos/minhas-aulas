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


def slugify(name: str) -> str:
    return name


def load_yaml(path: Path, default=None):
    if not path.exists():
        return default or {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def encontrar_arquivos(node):
    """Percorre a estrutura da aula (dicts/listas aninhados) e coleta todo valor
    de uma chave 'arquivo', em qualquer secao (slides, exercicios, tarefa_complementar, etc.)."""
    achados = []
    if isinstance(node, dict):
        if isinstance(node.get("arquivo"), str):
            achados.append(node["arquivo"])
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
            disciplina.pop  # no-op to keep linters quiet
            disciplina["aulas"] = disciplina["aulas"]
            disciplina["aulas"]
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
