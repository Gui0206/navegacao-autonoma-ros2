"""Planejamento e exploração em coordenadas (linha, coluna)."""
from collections import deque

PASSOS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
INVERSO = {"up": "down", "down": "up", "left": "right", "right": "left"}
ORIGEM = (0, 0)


def vizinho(pos, direcao):
    dl, dc = PASSOS[direcao]
    return pos[0] + dl, pos[1] + dc


def rota_minima(mapa, inicio, alvo):
    """Busca em largura com desempate pela ordem fixa de PASSOS."""
    fila = deque([inicio])
    anterior = {inicio: None}
    while fila:
        atual = fila.popleft()
        if atual == alvo:
            rota = []
            while atual != inicio:
                atual, direcao = anterior[atual]
                rota.append(direcao)
            return rota[::-1]
        for direcao in PASSOS:
            prox = vizinho(atual, direcao)
            if prox not in anterior and mapa.get(prox) in ("f", "t", "r"):
                anterior[prox] = (atual, direcao)
                fila.append(prox)
    raise ValueError("O alvo é inalcançável a partir da origem.")


def explorar(sentir, mover):
    """DFS física. A pilha guarda posição, direção de retorno e vizinhos restantes."""
    mapa = {ORIGEM: "r"}
    visitados = set()
    pilha = []
    movimentos = 0
    alvo = None

    def observar(pos, retorno):
        nonlocal alvo
        leitura = sentir()
        for direcao in PASSOS:
            celula = vizinho(pos, direcao)
            valor = leitura[direcao]
            if valor not in ("b", "f", "t"):
                raise ValueError(f"Leitura inválida em {celula}: {valor}")
            if celula == ORIGEM and valor == "f":
                valor = "r"
            if celula in mapa and mapa[celula] != valor:
                raise RuntimeError(f"Leituras incompatíveis em {celula}")
            mapa[celula] = valor
            if valor == "t":
                alvo = celula
        visitados.add(pos)
        pilha.append((pos, retorno, iter(PASSOS)))

    observar(ORIGEM, None)
    while pilha:
        pos, retorno, direcoes = pilha[-1]
        for direcao in direcoes:
            prox = vizinho(pos, direcao)
            if prox not in visitados and mapa[prox] == "f":
                mover(direcao)
                movimentos += 1
                observar(prox, INVERSO[direcao])
                break
        else:
            pilha.pop()
            if retorno:
                mover(retorno)
                movimentos += 1
    if alvo is None:
        raise ValueError("Exploração concluída sem encontrar um alvo acessível.")
    return mapa, alvo, movimentos


def localizar(mapa, simbolo):
    (pos,) = [pos for pos, valor in mapa.items() if valor == simbolo]
    return pos


def desenhar(mapa):
    linhas, colunas = zip(*mapa)
    return ["".join(mapa.get((l, c), "?") for c in range(min(colunas), max(colunas)+1))
            for l in range(min(linhas), max(linhas)+1)]
