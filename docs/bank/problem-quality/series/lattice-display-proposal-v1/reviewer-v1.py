"""Finite source-bound common-term-first presentation proposal, not admission.

No frozen constructors or prior evidence are edited. The proposal changes only
the order of complete additive terms in all eight lattice-resolvent menus.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path
import sympy as sp

ROOT = Path(__file__).resolve().parents[4]
LITERAL = ROOT / 'scripts/bank/quality/series/mathematical/review-code/literal_math.py'
sys.path.insert(0, str(LITERAL.parent))
from literal_math import parse

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def artifact(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--stage', type=Path, required=True)
    cli.add_argument('--served', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    out = args.output.resolve()
    if out.exists():
        raise RuntimeError('Preserve prior evidence: output must be a new directory')
    out.mkdir(parents=True)
    source_files = [args.stage.resolve() / f for f in ['canonical-previews.jsonl', 'retained-originals.jsonl']]
    source = {r['problemId']: r for path in source_files for r in read_lines(path)}
    served = read_lines(args.served)
    records = []
    # Consume the complete rational term and complete hyperbolic fraction.
    # This rule applies to every choice, irrespective of answer correctness.
    additive = re.compile(r'^(- )?(\\frac\{\d+\}\{\d+\}) \+ (\\frac\{\\pi \\(?:coth|tanh)\{.*\}\}\{\d+\})$')
    for record in served:
        if record['familyId'] != 'm3-series-olympiad-lattice-resolvent':
            continue
        old = source[record['problemId']]
        choices, equivalences = [], []
        for choice in record['choices']:
            match = additive.fullmatch(choice['math'])
            replacement = (match[3] + (' - ' if match[1] else ' + ') + match[2]) if match else choice['math']
            before, after = parse(choice['math']), parse(replacement)
            assert before == after, (choice['math'], replacement)
            assert sp.simplify(before-after) == 0
            choices.append({**choice, 'math': replacement})
            equivalences.append({'choiceId': choice['choiceId'], 'before': choice['math'], 'after': replacement,
                                 'changed': replacement != choice['math'], 'beforeDecoded': sp.srepr(before),
                                 'afterDecoded': sp.srepr(after), 'difference': '0',
                                 'proof': 'Commutativity of addition; full literal expressions parse to the same exact symbolic value.'})
        assert any(x['changed'] for x in equivalences)
        records.append({'sourcePreview': {key: old[key] for key in ['problemId', 'problemRevision', 'contentHash', 'semanticHash']},
                        'sourceCanonicalSHA256': digest(canonical(old)), 'familyId': old['familyId'],
                        'sourceInstanceIndex': old.get('parameters', {}).get('instance'),
                        'statement': record['statement'], 'solutionSteps': record['solutionSteps'],
                        'choices': choices, 'answerChoiceId': old['answerChoiceId'],
                        'difficulty': old['difficulty'], 'pedagogy': old['pedagogy'],
                        'statementMeaningChanged': False, 'answerChanged': False, 'difficultyChanged': False,
                        'preserveSemanticLineage': True, 'equivalences': equivalences,
                        'newIndependentIdeaCredit': 0, 'requiresNewImmutableRevision': True})
        record['choices'] = choices
    assert len(records) == 8
    assert sum(len(r['equivalences']) for r in records) == 32
    payload = {'status': 'proposed-consistent-lattice-display-normalization-awaiting-independent-owner-peer',
               'scope': 'Eight complete served menus; exact equality checked for all 32 choices. Complete statements, worked solutions, correct choice IDs, difficulty and semantic lineage are inherited unchanged. This is a display proposal, not eight new mathematical derivations or admission.',
               'rule': 'In every additive lattice choice, write the complete hyperbolic term first and the rational zero-mode/endpoint correction second. Apply equally to correct and wrong choices; leave standalone terms as-is.',
               'motivation': 'A literal leading-sign predictor selected the correct correction in four finite cases, although the paired positive sums were not mathematical opposites. Standard mathematical term order removes that textual leading-sign relation without padding or changing values.',
               'sourceArtifacts': [artifact(p) for p in [*source_files, args.served.resolve(), LITERAL, Path(__file__).resolve()]],
               'counts': {'records': 8, 'literalChoiceEqualities': 32, 'changedChoiceExpressions': sum(e['changed'] for r in records for e in r['equivalences'])},
               'records': records, 'admitted': False, 'imported': 0, 'active': 0}
    (out / 'lattice-display-proposal.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False)+'\n')
    (out / 'proposed-served705.jsonl').write_text(''.join(json.dumps(r, separators=(',', ':'), ensure_ascii=False)+'\n' for r in served))
    print(json.dumps(payload['counts']))

if __name__ == '__main__':
    main()
