#!/usr/bin/env python3
"""
Verifica, disciplina por disciplina, se os slides-fonte (.pptx) foram revisados
depois da ultima publicacao no site, e atualiza o que estiver desatualizado.

Cada disciplina indica sua propria pasta de slides-fonte no _disciplina.yaml,
via a chave opcional 'fonte_slides' (caminho absoluto). Disciplinas sem essa
chave sao ignoradas - nada precisa ser hardcoded aqui por disciplina.

Casamento aula <-> arquivo fonte: pelo nome de arquivo declarado em
_aula.yaml -> slides.arquivo. O .pptx e procurado em dois layouts, nesta ordem:
  1) fonte_slides/<slug-da-aula>/<arquivo>  (uma pasta por aula, mesmo slug do
     content/ - layout usado pelo CEA055 desde 2026-08)
  2) fonte_slides/<arquivo>                 (pasta unica com todos os .pptx)

Rode: python scripts/atualizar_slides.py [--aplicar]
  sem --aplicar: so lista o que esta desatualizado (dry-run)
  com --aplicar: reconverte (LibreOffice), copia .pptx+.pdf para o content/
                 e finaliza rodando scripts/build.py
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"


def load_yaml(path: Path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def encontrar_pendencias():
    """Retorna lista de dicts: {disciplina, aula_slug, aula_titulo, src, dest_pptx, dest_pdf}
    para cada aula cujo .pptx fonte e mais novo que o publicado (ou que ainda nao
    foi publicado)."""
    pendencias = []
    for semestre_dir in sorted(CONTENT_DIR.iterdir()):
        if not semestre_dir.is_dir():
            continue
        for disciplina_dir in sorted(semestre_dir.iterdir()):
            if not disciplina_dir.is_dir():
                continue
            disc_meta = load_yaml(disciplina_dir / "_disciplina.yaml")
            fonte = disc_meta.get("fonte_slides")
            if not fonte:
                continue
            fonte_dir = Path(fonte)
            if not fonte_dir.exists():
                print(f"aviso: fonte_slides nao encontrada para {disciplina_dir.name}: {fonte_dir}")
                continue

            for aula_dir in sorted(disciplina_dir.iterdir()):
                if not aula_dir.is_dir():
                    continue
                aula_meta = load_yaml(aula_dir / "_aula.yaml")
                slides = aula_meta.get("slides") or {}
                nome_pptx = slides.get("arquivo")
                if not nome_pptx:
                    continue

                # layout 1: uma pasta por aula (mesmo slug do content/)
                # layout 2: pasta unica com todos os .pptx
                candidatos = [fonte_dir / aula_dir.name / nome_pptx, fonte_dir / nome_pptx]
                src_pptx = next((c for c in candidatos if c.exists()), None)
                if src_pptx is None:
                    print(f"aviso: slide fonte nao encontrado em nenhum layout -> {candidatos[0]} | {candidatos[1]}")
                    continue

                dest_pptx = aula_dir / nome_pptx
                desatualizado = (
                    not dest_pptx.exists()
                    or src_pptx.stat().st_mtime > dest_pptx.stat().st_mtime
                )
                if desatualizado:
                    nome_pdf = slides.get("arquivo_pdf") or (Path(nome_pptx).stem + ".pdf")
                    pendencias.append({
                        "disciplina": disc_meta.get("titulo", disciplina_dir.name),
                        "aula_slug": aula_dir.name,
                        "aula_titulo": aula_meta.get("titulo", aula_dir.name),
                        "src_pptx": src_pptx,
                        "dest_dir": aula_dir,
                        "dest_pptx": dest_pptx,
                        "dest_pdf": aula_dir / nome_pdf,
                    })
    return pendencias


def converter_para_pdf(pptx: Path, saida_dir: Path) -> Path:
    saida_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(saida_dir), str(pptx)],
        check=True,
        capture_output=True,
    )
    gerado = saida_dir / (pptx.stem + ".pdf")
    if not gerado.exists():
        raise RuntimeError(f"conversao nao gerou o PDF esperado: {gerado}")
    return gerado


def aplicar(pendencias):
    tmp_dir = ROOT / "_tmp_slides_convertidos"
    atualizados = []
    for p in pendencias:
        pdf_convertido = converter_para_pdf(p["src_pptx"], tmp_dir)
        p["dest_dir"].mkdir(parents=True, exist_ok=True)
        shutil.copy2(p["src_pptx"], p["dest_pptx"])
        shutil.copy2(pdf_convertido, p["dest_pdf"])
        atualizados.append(p)
        print(f"  atualizado: {p['aula_slug']} ({p['aula_titulo']})")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return atualizados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true", help="aplica as atualizacoes (sem isso, so lista)")
    parser.add_argument("--aula", action="append", default=None,
                         help="restringe a um slug de aula (repetivel); sem isso, processa todas as pendencias")
    args = parser.parse_args()

    pendencias = encontrar_pendencias()
    if args.aula:
        pendencias = [p for p in pendencias if p["aula_slug"] in args.aula]
    if not pendencias:
        print("Nada para atualizar - todos os slides publicados estao com a mesma data (ou mais novos) que a fonte.")
        return

    print(f"{len(pendencias)} aula(s) com slide mais novo que o publicado:")
    for p in pendencias:
        print(f"  - [{p['disciplina']}] {p['aula_slug']}: {p['aula_titulo']}")

    if not args.aplicar:
        print("\n(dry-run - rode com --aplicar para converter e copiar de fato)")
        return

    print("\nConvertendo e copiando...")
    atualizados = aplicar(pendencias)

    print("\nRodando scripts/build.py...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], check=True, cwd=ROOT)

    print(f"\nPronto: {len(atualizados)} aula(s) atualizada(s) e site reconstruido em docs/.")


if __name__ == "__main__":
    main()
