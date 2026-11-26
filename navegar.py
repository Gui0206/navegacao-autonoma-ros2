"""Cliente ROS 2 para o simulador Culling Games."""
import argparse
import json
from pathlib import Path
from time import monotonic

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from cg_interfaces.msg import RobotSensors
from cg_interfaces.srv import GetMap, MoveCmd

from labirinto import ORIGEM, PASSOS, desenhar, explorar, localizar, rota_minima, vizinho


class Navegador(Node):
    def __init__(self):
        super().__init__("navegador")
        self.comando = self.create_client(MoveCmd, "/move_command")
        self.ultima_pos = None
        self.chegou = False

    def chamar(self, cliente, pedido):
        if not cliente.wait_for_service(timeout_sec=15):
            raise RuntimeError(f"Serviço indisponível: {cliente.srv_name}")
        futuro = cliente.call_async(pedido)
        rclpy.spin_until_future_complete(self, futuro, timeout_sec=10)
        if not futuro.done():
            raise TimeoutError(cliente.srv_name)
        return futuro.result()

    def mapa_completo(self):
        cliente = self.create_client(GetMap, "/get_map")
        res = self.chamar(cliente, GetMap.Request())
        linhas, colunas = res.occupancy_grid_shape
        if len(res.occupancy_grid_flattened) != linhas * colunas:
            raise ValueError("Dimensões inconsistentes no mapa do simulador.")
        return {divmod(i, colunas): valor for i, valor in enumerate(res.occupancy_grid_flattened)}

    def mover(self, direcao):
        res = self.chamar(self.comando, MoveCmd.Request(direction=direcao))
        pos = tuple(map(int, res.robot_pos))
        if not res.success or (self.ultima_pos is not None and pos != vizinho(self.ultima_pos, direcao)):
            raise RuntimeError(f"Movimento {direcao} falhou em {pos}.")
        self.ultima_pos = pos
        # Usado somente para confirmar a chegada, nunca para escolher uma direção.
        self.chegou = pos == tuple(res.target_pos)

    def sentir(self):
        # Assinatura volátil criada após a confirmação do movimento. Leituras
        # enfileiradas na posição anterior não podem entrar nesta assinatura.
        mensagens = []
        sub = self.create_subscription(RobotSensors, "/culling_games/robot_sensors",
                                       mensagens.append, qos_profile_sensor_data)
        try:
            prazo = monotonic() + 10
            while not mensagens:
                restante = prazo - monotonic()
                if restante <= 0:
                    raise TimeoutError("Sensor sem resposta.")
                rclpy.spin_once(self, timeout_sec=restante)
            return {d: getattr(mensagens[-1], d) for d in PASSOS}
        finally:
            self.destroy_subscription(sub)


def executar(no, modo):
    if modo == "parte1":
        mapa = no.mapa_completo()
        inicio = localizar(mapa, "r")
        alvo = localizar(mapa, "t")
        no.ultima_pos = inicio
        exploracao = 0
    else:
        mapa, alvo, exploracao = explorar(no.sentir, no.mover)
        inicio = ORIGEM
    rota = rota_minima(mapa, inicio, alvo)
    for direcao in rota:
        no.mover(direcao)
    if not no.chegou:
        raise RuntimeError("A posição final diverge do alvo do simulador.")
    return dict(modo=modo, rota=rota, passos=len(rota), chegou=True,
                movimentos_exploracao=exploracao, posicao_final=no.ultima_pos,
                mapa=desenhar(mapa))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("modo", choices=["parte1", "parte2"])
    parser.add_argument("saida", type=Path)
    args = parser.parse_args()
    rclpy.init(args=[])
    no = Navegador()
    try:
        resultado = executar(no, args.modo)
        args.saida.write_text(json.dumps(resultado, indent=2) + "\n")
        print(f"{args.modo}: chegada confirmada em {resultado['passos']} passos de rota.")
    finally:
        no.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
