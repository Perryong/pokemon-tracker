import { z } from 'zod';

export const MarketIdSchema = z.string().max(80).regex(/^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*-[a-zA-Z0-9.]+$/);
export const MarketDateSchema = z.string().datetime({ offset: true });
export const cardmarketMetrics = ['avg', 'low', 'trend', 'avg1', 'avg7', 'avg30', 'avg-holo', 'low-holo', 'trend-holo', 'avg1-holo', 'avg7-holo', 'avg30-holo'] as const;
export const tcgplayerMetrics = ['lowPrice', 'midPrice', 'highPrice', 'marketPrice', 'directLowPrice'] as const;
const prices = z.record(z.enum([...cardmarketMetrics, ...tcgplayerMetrics]), z.number().finite().nonnegative());
export const MarketHealthSchema = z.object({ service: z.literal('market-prices'), schemaVersion: z.literal(1), mode: z.literal('reference'), source: z.literal('TCGdex') }).strict();
export const MarketCardSchema = z.object({
  schemaVersion: z.literal(1), mode: z.literal('reference'), source: z.literal('TCGdex'),
  card: z.object({ id: MarketIdSchema, name: z.string().trim().min(1).max(200) }).strict(),
  fetchedAt: MarketDateSchema,
  quotes: z.array(z.object({
    provider: z.enum(['cardmarket', 'tcgplayer']), currency: z.enum(['EUR', 'USD']),
    variant: z.string().min(1).max(80), updatedAt: MarketDateSchema.nullable(),
    freshness: z.enum(['current', 'stale', 'unknown']), prices,
  }).strict()).max(33),
}).strict();
export type MarketCard = z.infer<typeof MarketCardSchema>;
