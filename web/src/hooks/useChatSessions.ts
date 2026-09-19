/**
 * 多会话状态管理 Hook
 *
 * 支持：
 * - Map<sessionId, ChatState> 管理多会话
 * - 独立 AbortController 用于取消请求
 * - 会话切换和清理
 */

import { useCallback, useRef, useState } from "react";
import { RetrievedDoc } from "@/lib/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  retrieved_docs?: RetrievedDoc[];
  streaming?: boolean;
  latency_ms?: number;
}

export interface ChatState {
  messages: Message[];
  loading: boolean;
  abortController: AbortController | null;
}

export function useChatSessions() {
  // Map<sessionId, ChatState>
  const sessionsRef = useRef<Map<string, ChatState>>(new Map());
  const [, forceUpdate] = useState({});

  const getSession = useCallback((sessionId: string): ChatState => {
    if (!sessionsRef.current.has(sessionId)) {
      sessionsRef.current.set(sessionId, {
        messages: [],
        loading: false,
        abortController: null,
      });
    }
    return sessionsRef.current.get(sessionId)!;
  }, []);

  const updateSession = useCallback((sessionId: string, updater: (state: ChatState) => Partial<ChatState>) => {
    const current = getSession(sessionId);
    const updated = { ...current, ...updater(current) };
    sessionsRef.current.set(sessionId, updated);
    forceUpdate({});
  }, [getSession]);

  const setMessages = useCallback((sessionId: string, messages: Message[]) => {
    updateSession(sessionId, () => ({ messages }));
  }, [updateSession]);

  const setLoading = useCallback((sessionId: string, loading: boolean) => {
    updateSession(sessionId, () => ({ loading }));
  }, [updateSession]);

  const createAbortController = useCallback((sessionId: string): AbortController => {
    const controller = new AbortController();
    updateSession(sessionId, () => ({ abortController: controller }));
    return controller;
  }, [updateSession]);

  const abort = useCallback((sessionId: string) => {
    const state = getSession(sessionId);
    if (state.abortController) {
      state.abortController.abort();
      updateSession(sessionId, () => ({ abortController: null, loading: false }));
    }
  }, [getSession, updateSession]);

  const clearSession = useCallback((sessionId: string) => {
    const state = getSession(sessionId);
    state.abortController?.abort();
    sessionsRef.current.delete(sessionId);
    forceUpdate({});
  }, [getSession]);

  const clearAllSessions = useCallback(() => {
    sessionsRef.current.forEach((state) => {
      state.abortController?.abort();
    });
    sessionsRef.current.clear();
    forceUpdate({});
  }, []);

  return {
    getSession,
    setMessages,
    setLoading,
    createAbortController,
    abort,
    clearSession,
    clearAllSessions,
  };
}
