"""Private local CLI; only an explicit model option can make a model API call."""

import argparse
import os
import sys
from pydantic import ValidationError
from .contracts import MarketError
from .demo import SCENARIOS, run_scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synthetic Market Agent demo; no live marketplace authority."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--scenario", choices=SCENARIOS, default="qualified")
    demo.add_argument(
        "--model",
        help="Optional paid model API: openai:MODEL. Tools and data stay synthetic.",
    )
    server = sub.add_parser('serve', help='Private loopback fixture workflow and UI')
    server.add_argument('--workspace', default='market-operator-fixture')
    server.add_argument('--port', type=int, default=8790)
    server.add_argument('--dist', default='dist')
    server.add_argument('--reference-url', default=None)
    server.add_argument('--initialize-demo', action='store_true', help='Explicitly initialize disposable simulation data')
    args = parser.parse_args(argv)
    try:
        if args.command == 'serve':
            from .server import serve

            return serve(args)
        model = None
        if args.model:
            provider, separator, name = args.model.partition(":")
            if provider != "openai" or not separator or not name.strip():
                raise MarketError("unsupported_model")
            if not os.environ.get("OPENAI_API_KEY"):
                raise MarketError("missing_model_key")
            from langchain_openai import ChatOpenAI

            model = ChatOpenAI(model=name, timeout=30, max_retries=0, store=False)
        result = run_scenario(args.scenario, model=model)
        print(result.model_dump_json(indent=2))
        return 0
    except MarketError as e:
        print(e.code, file=sys.stderr)
        return (
            2
            if e.code in ("unsupported_model", "missing_model_key", "unknown_scenario")
            else 1
        )
    except ValidationError:
        print("invalid_fixture", file=sys.stderr)
        return 2
    except Exception:
        print("agent_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
