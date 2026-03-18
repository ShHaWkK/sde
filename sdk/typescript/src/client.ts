/**
 * SDE TypeScript SDK — HTTP client
 */
import {
  SdeDiffRequest,
  SdeDiffResult,
  SdeBatchItem,
  SdeBatchResponse,
  SdeClientOptions,
  SdeChunk,
  SdeHealthResponse,
  SdeDomain,
  SdeDiffOptions,
} from "./types";

const DEFAULT_BASE_URL = "http://localhost:8000";
const DEFAULT_TIMEOUT = 30_000;

export class SemanticDiff {
  private readonly baseUrl: string;
  private readonly timeout: number;
  private readonly headers: Record<string, string>;

  constructor(options: SdeClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.timeout = options.timeout ?? DEFAULT_TIMEOUT;
    this.headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...options.headers,
    };
  }

  /**
   * Compare two texts semantically.
   */
  async diff(
    textA: string,
    textB: string,
    options: {
      domain?: SdeDomain;
      explain?: boolean;
      chunkingStrategy?: SdeDiffOptions["chunking_strategy"];
      embeddingModel?: string;
      language?: string;
    } = {}
  ): Promise<SdeDiffResult> {
    const body: SdeDiffRequest = {
      version: "1.0",
      text_a: textA,
      text_b: textB,
      domain: options.domain ?? "default",
      options: {
        chunking_strategy: options.chunkingStrategy ?? "auto",
        embedding_model: options.embeddingModel ?? "all-MiniLM-L6-v2",
        explain: options.explain ?? false,
        language: options.language ?? "en",
      },
    };

    return this._post<SdeDiffResult>("/diff", body);
  }

  /**
   * Stream chunk results as they are computed (Server-Sent Events).
   * Returns an AsyncIterable of SdeChunk objects, ending with a final summary event.
   */
  async *diffStream(
    textA: string,
    textB: string,
    options: {
      domain?: SdeDomain;
      explain?: boolean;
      chunkingStrategy?: SdeDiffOptions["chunking_strategy"];
    } = {}
  ): AsyncIterable<SdeChunk | { event: "done"; overall: string; global_score: number; delta_index: number }> {
    const body: SdeDiffRequest = {
      version: "1.0",
      text_a: textA,
      text_b: textB,
      domain: options.domain ?? "default",
      options: {
        chunking_strategy: options.chunkingStrategy ?? "auto",
        explain: options.explain ?? false,
      },
    };

    const response = await fetch(`${this.baseUrl}/diff/stream`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new SdeError(`HTTP ${response.status}: ${text}`, response.status);
    }

    if (!response.body) {
      throw new SdeError("Response body is null");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data) {
              yield JSON.parse(data);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Compare multiple text pairs in a single request.
   */
  async batch(items: SdeBatchItem[]): Promise<SdeBatchResponse> {
    return this._post<SdeBatchResponse>("/batch", { items });
  }

  /**
   * Health check.
   */
  async health(): Promise<SdeHealthResponse> {
    return this._get<SdeHealthResponse>("/health");
  }

  /**
   * Get the SDE specification as a string.
   */
  async spec(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/spec`, {
      headers: { ...this.headers, Accept: "text/markdown" },
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!response.ok) {
      throw new SdeError(`HTTP ${response.status}`, response.status);
    }
    return response.text();
  }

  private async _post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      const text = await response.text();
      let detail = text;
      try {
        detail = JSON.parse(text).detail ?? text;
      } catch {}
      throw new SdeError(`HTTP ${response.status}: ${detail}`, response.status);
    }

    return response.json() as Promise<T>;
  }

  private async _get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: this.headers,
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      throw new SdeError(`HTTP ${response.status}`, response.status);
    }

    return response.json() as Promise<T>;
  }
}

export class SdeError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number
  ) {
    super(message);
    this.name = "SdeError";
  }
}
