from typing import Dict, Any, List, Tuple


class ChampionSelector:
    """
    Selects the champion model using deterministic multi-criteria ranking
    and enforces the 'Complexity Must Earn Its Place' baseline improvement gate.
    """

    def __init__(self, min_baseline_improvement_pct: float = 0.02) -> None:
        self.min_improvement_pct = min_baseline_improvement_pct

    def select_champion(self, competition_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        evaluated = [m for m in competition_results if m.get("status") == "EVALUATED" and m.get("wape") is not None]

        if not evaluated:
            return {
                "champion_model": None,
                "selection_reason": "No candidate models evaluated successfully.",
                "champion_evaluation": None,
                "competition_results": competition_results,
            }

        baseline_ids = {"NAIVE", "MOVING_AVERAGE", "SEASONAL_NAIVE"}
        baselines = [m for m in evaluated if m["model_id"] in baseline_ids]

        def _baseline_sort_key(x: Dict[str, Any]) -> Tuple[float, float]:
            w = float(x["wape"]) if x["wape"] is not None else 999.0
            s = float(x["stability_variance"]) if x.get("stability_variance") is not None else 0.0
            return (w, s)

        best_baseline = min(baselines, key=_baseline_sort_key) if baselines else (evaluated[0] if evaluated else None)
        baseline_wape = float(best_baseline["wape"]) if best_baseline and best_baseline["wape"] is not None else 0.0

        for m in competition_results:
            m_wape = m.get("wape")
            is_eval = m.get("status") == "EVALUATED"
            if is_eval and m_wape is not None and baseline_wape is not None and baseline_wape > 0:
                imp = (baseline_wape - float(m_wape)) / baseline_wape
                m["baseline_improvement_pct"] = round(float(imp), 4)
            else:
                m["baseline_improvement_pct"] = 0.0

        def _candidate_sort_key(x: Dict[str, Any]) -> Tuple[float, float, float]:
            w = float(x["wape"]) if x["wape"] is not None else 999.0
            s = float(x["stability_variance"]) if x.get("stability_variance") is not None else 999.0
            b = abs(float(x["bias"])) if x.get("bias") is not None else 999.0
            return (w, s, b)

        sorted_candidates = sorted(evaluated, key=_candidate_sort_key)
        top_candidate = sorted_candidates[0]

        if top_candidate["model_id"] in baseline_ids or best_baseline is None:
            champion = top_candidate
            reason = (
                f"Selected {champion['model_id']} baseline as top performing "
                f"model with WAPE={float(champion['wape']):.4f}."
            )
        else:
            improvement = float(top_candidate.get("baseline_improvement_pct", 0.0))
            if improvement >= self.min_improvement_pct:
                champion = top_candidate
                reason = (
                    f"Selected {champion['model_id']} because it achieved lowest WAPE "
                    f"({float(champion['wape']):.4f}), outperforming best baseline "
                    f"({best_baseline['model_id']}, WAPE={baseline_wape:.4f}) by "
                    f"{improvement * 100:.2f}% (exceeding {self.min_improvement_pct * 100:.1f}% threshold)."
                )
            else:
                champion = best_baseline
                reason = (
                    f"Selected {best_baseline['model_id']} baseline (WAPE={baseline_wape:.4f}) "
                    f"because top complex candidate ({top_candidate['model_id']}, "
                    f"WAPE={float(top_candidate['wape']):.4f}) failed to demonstrate required "
                    f"{self.min_improvement_pct * 100:.1f}% baseline improvement gate "
                    f"(actual improvement: {improvement * 100:.2f}%)."
                )

        return {
            "champion_model": champion["model_id"],
            "selection_reason": reason,
            "champion_evaluation": champion,
            "competition_results": competition_results,
        }
