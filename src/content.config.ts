import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const systems = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/systems' }),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    order: z.number(),
    tags: z.array(z.string()),
    glance: z.array(z.string()),
    keyFiles: z.array(z.object({ path: z.string(), note: z.string() })),
    status: z.enum(['draft', 'ready']).default('draft'),
  }),
});

export const collections = { systems };
