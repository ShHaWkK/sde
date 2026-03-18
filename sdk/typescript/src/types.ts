/**
 * SDE TypeScript SDK — Type definitions aligned with SDE-SPEC-v1
 */

export type SdeDomain = "default" | "legal" | "medical" | "code" | "journalism";

export type SdeChunkingStrategy =
  | "sentence"
  | "paragraph"
  | "sliding_window"
  | "auto";

export type SdeOverallVerdict =
  | "identical"
  | "semantic_shift"
  | "contradiction"
  | "unrelated";

export type SdeChunkVerdict =
  | "identical"
  | "semantic_shift"
  | "contradiction"
  | "added"
  | "removed";

export interface SdeDiffOptions {
  chunking_strategy?: SdeChunkingStrategy;
  embedding_model?: string;
  explain?: boolean;
  language?: string;
}

export interface SdeDiffRequest {
  version?: string;
  text_a: string;
  text_b: string;
  domain?: SdeDomain;
  options?: SdeDiffOptions;
}

export interface SdeChunk {
  id: number;
  a: string | null;
  b: string | null;
  score: number;
  verdict: SdeChunkVerdict;
  explanation: string | null;
  confidence: number;
}

export interface SdeDiffMetadata {
  model: string;
  processing_ms: number;
  chunk_count_a: number;
  chunk_count_b: number;
}

export interface SdeDiffResult {
  sde_version: string;
  overall: SdeOverallVerdict;
  global_score: number;
  delta_index: number;
  chunks: SdeChunk[];
  metadata: SdeDiffMetadata;
}

export interface SdeBatchItem {
  id?: string | number;
  text_a: string;
  text_b: string;
  domain?: SdeDomain;
  options?: SdeDiffOptions;
}

export interface SdeBatchResultItem {
  id?: string | number;
  result: SdeDiffResult | null;
  error: string | null;
}

export interface SdeBatchResponse {
  results: SdeBatchResultItem[];
  total: number;
  failed: number;
}

export interface SdeClientOptions {
  baseUrl?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface SdeHealthResponse {
  status: string;
  version: string;
}
