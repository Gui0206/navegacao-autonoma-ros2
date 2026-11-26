"""Teste em memória dos algoritmos nos CSVs distribuídos com o simulador."""
import argparse
import csv
from pathlib import Path

from labirinto import ORIGEM, PASSOS, explorar, localizar, rota_minima, vizinho


def conferir(arquivo):
    with arquivo.open() as entrada:
        mapa = {(l, c): valor for l, linha in enumerate(csv.reader(entrada))
                for c, valor in enumerate(linha)}
    inicio = pos = localizar(mapa, "r")
    alvo = localizar(mapa, "t")
    referencia = rota_minima(mapa, inicio, alvo)

    def sentir():
        leitura = {d: mapa.get(vizinho(pos, d), "b") for d in PASSOS}
        return {d: "f" if v == "r" else v for d, v in leitura.items()}

    def mover(direcao):
        nonlocal pos
        assert pos != alvo
        pos = vizinho(pos, direcao)
        assert mapa.get(pos) in ("r", "t", "f")

    descoberto, destino, movimentos = explorar(sentir, mover)
    assert pos == inicio
    for (l, c), valor in descoberto.items():
        assert mapa.get((inicio[0] + l, inicio[1] + c), "b") == valor
    rota = rota_minima(descoberto, ORIGEM, destino)
    assert rota == referencia
    for direcao in rota:
        mover(direcao)
    assert pos == alvo
    return movimentos, len(rota)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("diretorio", type=Path)
    arquivos = sorted(parser.parse_args().diretorio.glob("*.csv"))
    if not arquivos:
        raise SystemExit("Nenhum CSV encontrado.")
    print("Mapa | Movimentos de exploração | Passos da rota validada")
    for arquivo in arquivos:
        movimentos, passos = conferir(arquivo)
        print(f"{arquivo.name} | {movimentos} | {passos}")
