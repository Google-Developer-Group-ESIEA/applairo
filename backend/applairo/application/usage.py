# application/usage.py
# Tarification et coût d'un appel LLM.
#
# Purement APPLICATIF : traduit une consommation de tokens (TokenUsage, domaine)
# en un montant USD selon une grille (Pricing, issue de la config). Le domaine
# ignore les prix ; l'adaptateur ADK ignore les prix : c'est ici, dans le cas
# d'usage, qu'on assemble « tokens + modèle + coût » à afficher.

from dataclasses import dataclass

from applairo.domain.models import TokenUsage


@dataclass(frozen=True)
class Pricing:
    """Grille tarifaire d'un modèle (USD par million de tokens)."""

    input_usd_per_mtok: float
    output_usd_per_mtok: float

    def cost_usd(self, usage: TokenUsage) -> float:
        """Coût en USD d'un appel, entrée + sortie (réflexion incluse dans output)."""
        return (
            usage.prompt * self.input_usd_per_mtok + usage.output * self.output_usd_per_mtok
        ) / 1_000_000


@dataclass(frozen=True)
class CallUsage:
    """Consommation d'UN appel, prête à afficher : modèle, tokens et coût USD."""

    model: str
    prompt_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float

    @classmethod
    def of(cls, model: str, usage: TokenUsage, pricing: Pricing) -> "CallUsage":
        return cls(
            model=model,
            prompt_tokens=usage.prompt,
            output_tokens=usage.output,
            total_tokens=usage.total,
            cost_usd=pricing.cost_usd(usage),
        )
