#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/.."
mapa=${1:-test.csv}
saida=${2:-resultado}
mkdir -p "$saida"
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-76}
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
pid=
encerrar() {
    if [[ -n "$pid" ]]; then
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
        pid=
    fi
}
trap encerrar EXIT
# Executar diretamente evita deixar o processo filho de 'ros2 run' ativo.
jogo="$(ros2 pkg prefix cg)/lib/cg/maze"
for parte in parte1 parte2; do
    "$jogo" --map "$mapa" >"$saida/$parte.log" 2>&1 &
    pid=$!
    python3 navegar.py "$parte" "$saida/$parte.json"
    encerrar
done
python3 - "$saida" <<'PY'
import json, sys
from pathlib import Path
pasta = Path(sys.argv[1])
a, b = [json.loads((pasta / f"parte{i}.json").read_text()) for i in (1, 2)]
if a["rota"] != b["rota"] or a["posicao_final"] != b["posicao_final"]:
    raise SystemExit("Falha: rotas ou destinos divergentes.")
print(f"Rotas idênticas: {a['passos']} passos até {a['posicao_final']}.")
PY
