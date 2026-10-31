"""Offline scenarios: real Deep Agents graph, scripted model and simulated seller."""
import argparse
from datetime import datetime, timezone
from importlib.resources import files
import json
from langchain_core.messages import AIMessage
from .controlled import ControlledModel
from .harness import run_session
from .session import SalesSession, SimulatedSeller


def tool_call(name, **args):
    return AIMessage(content='', tool_calls=[{'name': name, 'args': args,
        'id': f'fixture-{name}', 'type': 'tool_call'}])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=['eligible', 'out-of-policy', 'expired', 'opt-out', 'material-facts'], default='eligible')
    parser.add_argument('--fixture', help='Local JSON lead/mandate/current/seller_replies fixture')
    args = parser.parse_args()
    if args.fixture:
        with open(args.fixture, encoding='utf-8') as f: data = json.load(f)
    else:
        data = json.loads(files('pokemon_sales').joinpath('fixtures/qualified_lead.json').read_text())
    now = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
    if args.scenario == 'expired':
        data['mandate']['expires_at'] = '2026-10-29T12:00:00Z'
    if args.scenario == 'opt-out':
        data['seller_replies'] = [{'text': 'Please stop contacting me.', 'opt_out': True}]
    if args.scenario == 'material-facts':
        data['seller_replies'] = [{'text': 'There is a crease.', 'material_facts': {'condition': 'creased'}}]
    s = SalesSession(lead=data['lead'], mandate=data['mandate'], current=data['current'],
                     seller=SimulatedSeller(data['seller_replies']), clock=lambda: now)
    cid = s.lead.conversation_id
    price = 5001 if args.scenario == 'out-of-policy' else 4500
    model = ControlledModel(responses=[
        tool_call('ask_question', conversation_id=cid, topic='condition'),
        tool_call('propose_price', conversation_id=cid, amount_minor=price),
        tool_call('prepare_proposal', conversation_id=cid, amount_minor=price),
        AIMessage(content='Fixture scenario finished.')])
    result = run_session(s, model)
    result.update(scenario=args.scenario, model_transport='scripted_offline_fixture',
                  clock='fixed_demo_time_2026-10-29T12:00:00Z')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
