"""In-container plugin entrypoint (Constitution Principle II).

Executed *inside* a disposable LXD container by the LXD backend. It registers the
built-in plugins, runs exactly one plugin against the injected candidate source,
and prints the structured result as JSON on stdout so the host can read back only
``{grade, pros, cons}`` — never executing candidate code on the host.

Usage (inside the container):
    python -m src.runners.in_container <plugin_key> <submission_path> [config_json]
"""
from __future__ import annotations

import json
import sys

from src.tests_plugins.registry import PluginInput, registry


def _register_all() -> None:
    # Register the same built-in plugins the API registers, without importing the
    # FastAPI app (keeps the container entrypoint dependency-light).
    from src.tests_plugins import ai_agent_example, metric_example
    from src.tests_plugins.quality.builtin import register_quality_plugins

    register_quality_plugins(registry)
    for mod in (ai_agent_example, metric_example):
        if mod.KEY not in registry.keys():
            registry.register(mod.KEY, mod.factory)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(json.dumps({"error": "usage: in_container <key> <path> [config_json]"}))
        return 2
    key = argv[1]
    submission_path = argv[2]
    config = json.loads(argv[3]) if len(argv) > 3 and argv[3] else {}

    _register_all()
    try:
        plugin = registry.create(key)
    except KeyError:
        print(json.dumps({"error": f"unknown plugin: {key}"}))
        return 3

    output = plugin.run(PluginInput(submission_path=submission_path, config=config))
    print(json.dumps({"grade": output.grade, "pros": output.pros, "cons": output.cons, "log": getattr(output, "log", "")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
