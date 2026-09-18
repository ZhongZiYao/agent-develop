/** 与 FastAPI 后端交互的 API 客户端 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface RetrievedDoc {
  id: string;
  title: string;
  content: string;
  source: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface QueryResponse {
  answer: string;
  thinking?: string;
  has_thinking?: boolean;
  retrieved_docs: RetrievedDoc[];
  citations: number[];
  trace_id: string;
  usage: Record<string, number>;
  latency_ms: number;
}

export interface IndexResponse {
  job_id: string;
  status: string;
  total_docs: number;
  total_chunks: number;
  started_at: string;
  finished_at?: string;
}

export interface HealthResponse {
  status: string;
  components: Record<string, string>;
  version: string;
  vector_count: number;
}

// ===== 同步问答 =====
export async function query(params: {
  query: string;
  game?: string;
  top_k?: number;
  top_n?: number;
}): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      game: params.game || null,
      top_k: params.top_k ?? 10,
      top_n: params.top_n ?? 5,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Query failed: ${err}`);
  }
  return res.json();
}

// ===== 流式问答（SSE） =====
export async function* streamQuery(params: {
  query: string;
  game?: string;
  top_k?: number;
  top_n?: number;
}): AsyncGenerator<{
  event: string;
  data: Record<string, unknown>;
}> {
  const res = await fetch(`${API_BASE}/api/v1/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      game: params.game || null,
      top_k: params.top_k ?? 10,
      top_n: params.top_n ?? 5,
    }),
  });

  if (!res.ok || !res.body) {
    throw new Error("Stream failed");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 格式：event:xxx\ndata:xxx\n\n
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        const dataStr = line.slice(5).trim();
        try {
          const data = JSON.parse(dataStr);
          yield { event: currentEvent, data };
        } catch {
          // skip malformed
        }
        currentEvent = "";
      }
    }
  }
}

// ===== 触发索引 =====
export async function buildIndex(params: {
  source_dir?: string;
  force_rebuild?: boolean;
}): Promise<IndexResponse> {
  const res = await fetch(`${API_BASE}/api/v1/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source_dir: params.source_dir || null,
      force_rebuild: params.force_rebuild ?? false,
    }),
  });
  if (!res.ok) throw new Error("Index failed");
  return res.json();
}

export async function getIndexStatus(jobId: string): Promise<IndexResponse> {
  const res = await fetch(`${API_BASE}/api/v1/index/${jobId}`);
  if (!res.ok) throw new Error("Status query failed");
  return res.json();
}

// ===== 健康检查 =====
export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  return res.json();
}