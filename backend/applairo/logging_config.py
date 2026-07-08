# applairo/logging_config.py
# Configuration du logging applicatif.
#
# On configure uniquement le logger racine « applairo » (pas le root global) :
# les modules récupèrent un logger enfant via logging.getLogger(__name__), donc
# tous héritent de ce handler. propagate=False évite les doublons avec les
# handlers d'uvicorn.

import logging
import sys

_LOGGER_NAME = "applairo"


def configure_logging(level: str) -> None:
    """Configure le logger applicatif « applairo » (idempotent)."""
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level.upper())

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)

    logger.propagate = False
