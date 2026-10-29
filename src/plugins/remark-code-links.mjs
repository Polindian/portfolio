// Turns markdown links like [`DetermineRoundWinner`](code:AChrisGameMode::DetermineRoundWinner)
// into GitHub permalinks to the exact lines, using src/data/code-refs.json.
// The build fails on an unknown symbol, so a link can never point at the wrong place.
import { readFileSync } from 'node:fs';

const REPO = 'https://github.com/Polindian/AnimationTesting';

export default function remarkCodeLinks() {
  const { ref: REF, symbols: refs } = JSON.parse(readFileSync(new URL('../data/code-refs.json', import.meta.url), 'utf-8'));

  const visit = (node, file) => {
    if (node.type === 'link' && node.url.startsWith('code:')) {
      const symbol = node.url.slice(5).trim();
      const ref = refs[symbol];
      if (!ref) {
        throw new Error(`Unknown code link "${symbol}" in ${file.path}. Run scripts/gen-code-refs.py.`);
      }
      node.url = `${REPO}/blob/${REF}/${ref.path}#L${ref.start}-L${ref.end}`;
      node.data = { hProperties: { class: 'code-link', target: '_blank', rel: 'noopener', title: `${ref.path.split('/').pop()}, lines ${ref.start}–${ref.end}` } };
    }
    for (const child of node.children ?? []) visit(child, file);
  };

  return (tree, file) => visit(tree, file);
}
