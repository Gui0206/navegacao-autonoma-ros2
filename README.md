# Navegação autônoma em labirinto com ROS 2

O robô resolve o mesmo labirinto em duas partidas no simulador [Culling Games](https://github.com/rmnicola/culling_games). Na primeira, recebe o mapa completo. Na segunda, parte de uma célula desconhecida, constrói um mapa pelos sensores e usa esse mapa para chegar ao alvo.

## Parte 1 · Menor caminho com mapa conhecido

O cliente consulta `/get_map`, reconstrói a matriz em ordem de linha e localiza robô e alvo. Cada célula transitável é um vértice. Duas células compartilham uma aresta quando permitem um movimento horizontal ou vertical entre elas. Cada movimento custa um passo.

A busca em largura (BFS) visita os vértices por distância crescente da origem. Ao alcançar o alvo, a cadeia de predecessores fornece uma rota com o menor número de passos. O robô executa cada comando em `/move_command` e verifica o resultado. O custo da busca é O(V + E) em tempo e O(V) em memória.

## Parte 2 · Exploração e reprodução

O robô adota sua posição inicial como (0, 0). Em cada nova célula, lê os quatro vizinhos cardeais em `/culling_games/robot_sensors`. A exploração em profundidade (DFS) avança por corredores livres ainda não visitados e desfaz fisicamente cada movimento para retornar à bifurcação anterior. Ao avistar o alvo, registra sua posição e adia a entrada até o fim da exploração, pois entrar nele encerra a partida.

Quando a pilha esvazia, o robô está novamente na origem. O mapa contém todas as células alcançáveis antes de entrar no alvo e as paredes observadas ao redor delas. Todo caminho mínimo até o alvo passa apenas por essas células. Assim, a BFS sobre o mapa descoberto tem informação suficiente para reproduzir a rota da parte 1. A ordem de desempate é cima, baixo, esquerda e direita nas duas buscas. Os movimentos de ida e volta da exploração são contados separadamente dos passos da rota final.

A parte 2 pode ser executada sozinha. O planejador recebe exclusivamente o mapa sensorial. A comparação dos arquivos das duas partidas acontece depois da chegada.

## Reproduzir no Linux

Use Ubuntu 24.04 com ROS 2 Jazzy, `colcon`, Git e Python 3. A partir da raiz deste repositório, prepare o simulador em um diretório vizinho.

```bash
sudo apt-get install python3-pygame
source /opt/ros/jazzy/setup.bash
git clone https://github.com/rmnicola/culling_games.git ../culling_games
git -C ../culling_games checkout a6c182a74606bcd80d24fc3a20710b55decc863a
(cd ../culling_games && colcon build --packages-select cg_interfaces cg)
source ../culling_games/install/setup.bash
bash scripts/demonstrar.sh 1.csv
```

O script inicia uma instância nova do simulador para cada parte. A janela Pygame mostra a navegação. Para executar sem tela, use `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy bash scripts/demonstrar.sh 1.csv`. O primeiro argumento escolhe o CSV e o segundo escolhe o diretório dos resultados (padrão `resultado/`). Use um domínio ROS livre. O script usa o domínio 76 por padrão.

Para executar uma única parte, abra o jogo com `ros2 run cg maze --map 1.csv` e, em outro terminal com o mesmo ambiente ROS, rode `python3 navegar.py parte2 parte2.json` ou `python3 navegar.py parte1 parte1.json`. Inicie cada parte com o robô na posição original.

## Conferir a evidência

No mapa oficial `1.csv`, o robô alcançou a célula (14, 14) nas duas partidas. A parte 2 fez 780 movimentos para explorar e voltar à origem. Em seguida, reproduziu os mesmos 102 comandos da parte 1. A execução usou ROS 2 Jazzy em um contêiner Linux, com Pygame em modo sem tela. Consulte a [partida com mapa completo](evidencias/ros2-1/parte1.json) e a [partida com mapa descoberto](evidencias/ros2-1/parte2.json).

Os arquivos JSON de cada partida contêm o mapa, a sequência ordenada de comandos, a posição final informada pelo simulador e as contagens de movimentos. No mapa, `r` marca a origem, `t` o alvo, `f` um espaço livre, `b` uma parede e `?` uma célula sem observação. As coordenadas finais do serviço ROS são absolutas, em linha e coluna, com índice inicial zero.

O teste em memória percorre os 11 CSVs oficiais. Para cada um, verifica as leituras do mapa reconstruído, o retorno à origem, a igualdade exata das rotas e a chegada ao alvo. Os resultados estão em [evidencias/testes.txt](evidencias/testes.txt).

```bash
python3 verificar_mapas.py ../culling_games/src/cg/maps
```
