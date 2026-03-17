import { z } from 'zod';

export const capabilityRequestSchema = z.object({
  capability: z.string().min(1).max(64),
  input: z.record(z.string(), z.unknown()),
  request_id: z.string().max(128).optional()
}).strict();

export const summaryInputSchema = z.object({
  text: z.string().trim().min(1).max(20000),
  max_length: z.number().int().min(20).max(1000).default(120)
}).strict();

export const keywordsInputSchema = z.object({
  text: z.string().trim().min(1).max(20000),
  top_k: z.number().int().min(1).max(20).default(5)
}).strict();
