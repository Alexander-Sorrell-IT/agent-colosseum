"""Agent Colosseum — you talk to ONE mind whose cognition is a catalog of models.

The package no longer eagerly imports the legacy simulation stack: doing so dragged the
rejected multi-model-comparison build into the import path of the VISION engine. Import what
you need directly, e.g. `from colosseum.mind import Mind`. (Legacy modules remain importable
by their own paths until they are removed per VISION's teardown plan.)
"""
