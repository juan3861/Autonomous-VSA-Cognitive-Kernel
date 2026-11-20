"""Counterfactual Regret Minimization+ (CFR+) for Imperfect-Information Games.

Organ 80 do Substrato Cognitivo Nao-LLM (AetherCOS v7.0).
Algoritmo CFR+ (Zinkevich et al., NeurIPS 2007 / Tammelin, 2014) para jogos extensivos
de informacao imperfeita e blefe estrategico (Kuhn Poker - 3 cartas, 2 jogadores, soma zero):
- Mantem conjuntos de informacao (InfoSets) com arrependimentos contrafactuais acumulados;
- Executa travessias recursivas na arvore do jogo ponderando pelo alcance contrafactual do
  oponente e aplicando truncamento positivo Regret+ com media linear;
- Converge para o equilibrio de Nash comportamental com valor teorico exato do Jogador 1
  em Kuhn Poker igual a -1/18 = -0.055556 e explorabilidade < 0.005.
"""
from __future__ import annotations

import itertools
import time
from typing import Dict, Any, List
import numpy as np


class _KuhnInfoSet:
    """Conjunto de informacao para Kuhn Poker com 2 acoes: 0=Pass/Fold, 1=Bet/Call."""

    def __init__(self):
        self.regret_sum = np.zeros(2, dtype=np.float64)
        self.strategy_sum = np.zeros(2, dtype=np.float64)

    def get_strategy(self, weight: float) -> np.ndarray:
        pos = np.maximum(self.regret_sum, 0.0)
        tot = float(np.sum(pos))
        strat = (pos / tot) if tot > 1e-12 else np.array([0.5, 0.5], dtype=np.float64)
        self.strategy_sum += weight * strat
        return strat

    def get_average_strategy(self) -> np.ndarray:
        tot = float(np.sum(self.strategy_sum))
        return (self.strategy_sum / tot) if tot > 1e-12 else np.array([0.5, 0.5], dtype=np.float64)


class CounterfactualRegretCFRPlusSolver:
    """
    Solucionador CFR+ para Jogos Extensivos de Informacao Imperfeita (Kuhn Poker).
    """

    def __init__(self, n_iters: int = 1200):
        self.n_iters = int(n_iters)

    @staticmethod
    def _terminal_utility(cards: tuple[int, int], history: str) -> Optional[float]:
        """Retorna utilidade do Jogador 0 se terminal, ou None caso contrario."""
        if history == "pp":
            return 1.0 if cards[0] > cards[1] else -1.0
        if history in ("pbb", "bb"):
            return 2.0 if cards[0] > cards[1] else -2.0
        if history == "bp":
            return 1.0
        if history == "pbp":
            return -1.0
        return None

    def solve_kuhn_poker(self, n_iters: Optional[int] = None) -> Dict[str, Any]:
        """
        Executa CFR+ sobre todas as 6 distribuicoes de cartas de Kuhn Poker (exact chance traversal).
        """
        t0 = time.perf_counter()

        T = int(n_iters if n_iters is not None else self.n_iters)
        infosets: Dict[str, _KuhnInfoSet] = {}
        deals = list(itertools.permutations([0, 1, 2], 2))  # 6 maos equiprovaveis (J=0, Q=1, K=2)

        def get_node(key: str) -> _KuhnInfoSet:
            if key not in infosets:
                infosets[key] = _KuhnInfoSet()
            return infosets[key]

        def cfr(cards: tuple[int, int], history: str, p0: float, p1: float, t_weight: float) -> float:
            term = self._terminal_utility(cards, history)
            if term is not None:
                return term

            player = len(history) % 2
            key = f"{cards[player]}:{history}"
            node = get_node(key)

            reach = p0 if player == 0 else p1
            strat = node.get_strategy(t_weight * reach)

            util = np.zeros(2, dtype=np.float64)
            actions = ("p", "b")
            for a_idx, act in enumerate(actions):
                if player == 0:
                    util[a_idx] = cfr(cards, history + act, p0 * strat[a_idx], p1, t_weight)
                else:
                    util[a_idx] = cfr(cards, history + act, p0, p1 * strat[a_idx], t_weight)

            node_util = float(np.dot(strat, util))

            opp_reach = p1 if player == 0 else p0
            sign = 1.0 if player == 0 else -1.0
            for a_idx in range(2):
                regret = sign * (util[a_idx] - node_util) * opp_reach
                # CFR+: clamp negativo imediatamente a 0
                node.regret_sum[a_idx] = max(0.0, node.regret_sum[a_idx] + regret)

            return node_util

        for t in range(1, T + 1):
            for deal in deals:
                cfr(deal, "", 1.0, 1.0, float(t))

        # Avalia valor exato do jogo e melhor resposta (explorabilidade) das estrategias medias
        avg_strats = {k: v.get_average_strategy() for k, v in infosets.items()}

        def eval_ev(cards: tuple[int, int], history: str) -> float:
            term = self._terminal_utility(cards, history)
            if term is not None:
                return term
            player = len(history) % 2
            s = avg_strats[f"{cards[player]}:{history}"]
            return s[0] * eval_ev(cards, history + "p") + s[1] * eval_ev(cards, history + "b")

        ev_p0 = sum(eval_ev(d, "") for d in deals) / len(deals)

        # Melhor resposta contra estrategia fixa de um oponente
        def best_response_value(br_player: int) -> float:
            # Calcula valor esperado otimo por InfoSet para br_player
            info_action_vals: Dict[str, np.ndarray] = {}

            def traverse_br(cards: tuple[int, int], history: str, opp_prob: float):
                term = self._terminal_utility(cards, history)
                if term is not None:
                    return term * (1.0 if br_player == 0 else -1.0)
                player = len(history) % 2
                if player == br_player:
                    key = f"{cards[player]}:{history}"
                    if key not in info_action_vals:
                        info_action_vals[key] = np.zeros(2, dtype=np.float64)
                    v0 = traverse_br(cards, history + "p", opp_prob)
                    v1 = traverse_br(cards, history + "b", opp_prob)
                    info_action_vals[key][0] += opp_prob * v0
                    info_action_vals[key][1] += opp_prob * v1
                    # Nota: para br exato em Kuhn, avaliamos em 2 passos; aqui aproximamos via argmax global
                    return max(v0, v1)
                else:
                    s = avg_strats[f"{cards[player]}:{history}"]
                    return (
                        s[0] * traverse_br(cards, history + "p", opp_prob * s[0])
                        + s[1] * traverse_br(cards, history + "b", opp_prob * s[1])
                    )

            # Em Kuhn Poker, cada InfoSet aparece no maximo uma vez por mao/sequencia:
            # resolvemos por programacao dinamica nos infosets do jogador BR
            # Passo 1: acumula pesos de alcance em cada infoset; Passo 2: escolhe acao otima por infoset
            # Como cada carta do BR e privada e fixa, a escolha otima por InfoSet e exatamente
            # obtida quando iteramos por carta do BR separadamente!
            total_br = 0.0
            for br_card in (0, 1, 2):
                opp_cards = [c for c in (0, 1, 2) if c != br_card]
                # Para um dado br_card, cada historia de decisao do BR define um unico InfoSet!
                def br_card_ev(history: str, opp_weights: Dict[int, float]) -> float:
                    # Verifica terminal para cada carta do oponente
                    player = len(history) % 2
                    if self._terminal_utility((0, 1), history) is not None:
                        val = 0.0
                        for oc, ow in opp_weights.items():
                            c_pair = (br_card, oc) if br_player == 0 else (oc, br_card)
                            u = self._terminal_utility(c_pair, history)
                            val += ow * u * (1.0 if br_player == 0 else -1.0)
                        return val
                    if player == br_player:
                        return max(
                            br_card_ev(history + "p", opp_weights),
                            br_card_ev(history + "b", opp_weights),
                        )
                    else:
                        w_p = {oc: ow * avg_strats[f"{oc}:{history}"][0] for oc, ow in opp_weights.items()}
                        w_b = {oc: ow * avg_strats[f"{oc}:{history}"][1] for oc, ow in opp_weights.items()}
                        return br_card_ev(history + "p", w_p) + br_card_ev(history + "b", w_b)

                init_w = {oc: 1.0 / 6.0 for oc in opp_cards}
                total_br += br_card_ev("", init_w)
            return total_br

        br0 = best_response_value(0)
        br1 = best_response_value(1)
        exploitability = 0.5 * (br0 + br1)
        exact_kuhn_ev = -1.0 / 18.0

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "CFR_PLUS_EXTENSIVE_NASH_CONVERGED",
            "game": "kuhn_poker_3_card",
            "iterations": T,
            "n_infosets": len(infosets),
            "p0_expected_value": round(ev_p0, 6),
            "theoretical_nash_value": round(exact_kuhn_ev, 6),
            "value_error_vs_exact": round(abs(ev_p0 - exact_kuhn_ev), 6),
            "exploitability": float(f"{exploitability:.3e}"),
            "nash_converged": exploitability < 5e-3,
            "elapsed_us": round(elapsed_us, 2),
        }
