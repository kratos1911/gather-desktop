"""Compare synthetic baseline/candidate vectors after an inference-stack upgrade."""
import json
import math

from scripts.prepare_inference_image import ROOT, digest


def main():
    root = ROOT / 'output/inference-results'
    paths = [root / 'compatibility-vectors.json', root / 'patched/compatibility-vectors.json']
    old, new = [json.loads(path.read_text()) for path in paths]
    if len(old) != 6 or len(new) != 6:
        raise ValueError('Six completed compatibility cases required')
    cosines, deltas = [], []
    for before, after in zip(old, new):
        for key in ('model', 'revision', 'dimensions', 'prompt_tokens'):
            if before[key] != after[key]:
                raise ValueError('Model identity or tokenizer count changed')
        a, b = before['data'][0]['embedding'], after['data'][0]['embedding']
        if len(a) != 512 or len(b) != 512 or not all(math.isfinite(x) for x in a + b):
            raise ValueError('Invalid compatibility vectors')
        cosines.append(sum(x*y for x, y in zip(a, b)) / (math.hypot(*a) * math.hypot(*b)))
        deltas.append(max(abs(x-y) for x, y in zip(a, b)))
    def ranks(results):
        vectors = [item['data'][0]['embedding'] for item in results]
        return [sorted((0, 2, 4), key=lambda d: -sum(x*y for x, y in zip(vectors[q], vectors[d])))
                for q in (1, 3, 5)]
    report = {'scope': 'six synthetic cases; not full retrieval regression',
              'baseline_vectors_sha256': digest(paths[0]), 'candidate_vectors_sha256': digest(paths[1]),
              'cosines': cosines, 'max_absolute_deltas': deltas,
              'baseline_ranks': ranks(old), 'candidate_ranks': ranks(new),
              'token_counts_equal': True,
              'passed': min(cosines) >= .99999 and max(deltas) <= .0001 and ranks(old) == ranks(new)}
    destination = root / 'patched/compatibility-comparison.json'
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if not report['passed']:
        raise SystemExit('Upgrade compatibility gate failed')


if __name__ == '__main__':
    main()
