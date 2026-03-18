/**
 * @semantic-diff/core — TypeScript SDK for the Semantic Diff Engine
 *
 * @example
 * ```typescript
 * import { SemanticDiff } from '@semantic-diff/core'
 *
 * const sde = new SemanticDiff({ baseUrl: 'http://localhost:8000' })
 * const result = await sde.diff(textA, textB, { domain: 'legal', explain: true })
 * console.log(result.overall, result.global_score)
 * ```
 */
export { SemanticDiff, SdeError } from "./client";
export type {
  SdeDiffResult,
  SdeChunk,
  SdeChunkVerdict,
  SdeOverallVerdict,
  SdeDomain,
  SdeDiffRequest,
  SdeDiffOptions,
  SdeDiffMetadata,
  SdeBatchItem,
  SdeBatchResponse,
  SdeBatchResultItem,
  SdeClientOptions,
  SdeChunkingStrategy,
  SdeHealthResponse,
} from "./types";
