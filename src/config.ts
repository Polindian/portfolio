import codeRefs from './data/code-refs.json';

// One place for links, so swapping to a showcase repo or custom domain is a one-line change.
export const SITE = {
  name: 'Christopher Naglik',
  role: 'Junior Gameplay & Multiplayer Programmer',
  stack: 'Unreal Engine 5 · C++ · GAS · Dedicated Servers',
  email: 'TODO@example.com',
  linkedin: 'https://www.linkedin.com/in/TODO',
  github: 'https://github.com/Polindian',
  steam: '', // fill when the store page is live
  trailerYouTubeId: '', // e.g. 'dQw4w9WgXcQ'
};

// Code links point at a tag, so they never break as the code changes.
export const CODE = {
  repo: 'https://github.com/Polindian/AnimationTesting',
  ref: codeRefs.ref, // set by scripts/gen-code-refs.py from the game repo's tag
  sourceRoot: 'Source/AnimationTesting/Private',
};

export const codeUrl = (path: string, lines?: string) =>
  `${CODE.repo}/blob/${CODE.ref}/${path.startsWith('Source') || path.startsWith('ServerDeploy') ? path : `${CODE.sourceRoot}/${path}`}${lines ? `#${lines}` : ''}`;
