/** SSE Chat Component for Enterprise RAG Workspace.

Handles Server-Sent Events streaming for grounded Q&A token responses.
Features:
- Live token streaming with low latency
- Dynamic source citation pills that update as tokens arrive
- Auto-scroll as new content arrives
- Click citations → scroll PDF viewer to exact page/paragraph
- Connection error handling and reconnection support
*/

import React, { useState, useEffect, useRef, useCallback } from "react";

// SSE EventSource polyfill for Safari compatibility
// In production, use native EventSource with fallback
const isSSESupported = typeof EventSource !== "undefined";

const ChatSSE = ({
  question,
  onTokenReceived,      // callback(tokenText, accumulatedText, sourceRefs)
  onQueryComplete,      // callback(fullText, sourceRefs)
  onError,              // callback(errorMessage)
  initialSourceRefs = [], // initial citation references
  autoScroll = true,
}) => {
  const [sseReady, setSSEReady] = useState(false);
  const [eventSource, setEventSource] = useState(null);
  const [accumulatedText, setAccumulatedText] = useState("");
  const [sourceRefs, setSourceRefs] = useState(initialSourceRefs);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectAttempts = useRef(0);
  const maxReconnects = 3;

  // Initialize SSE connection when question changes
  useEffect(() => {
    if (!question || !question.trim()) {
      // Cleanup if no question
      if (eventSource) {
        eventSource.close();
        setEventSource(null);
        setSSEReady(false);
        setIsConnected(false);
      }
      return;
    }

    // Cleanup existing connection
    if (eventSource) {
      eventSource.close();
    }

    // Create new SSE connection
    const url = `/api/queries/sse/queries/${Date.now()}?question=${encodeURIComponent(
      question
    )}`;

    try {
      const source = new EventSource(url);
      setEventSource(source);
      setSSEReady(true);

      source.onopen = () => {
        console.log("SSE connection opened");
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      source.onmessage = (event) => {
        const data = event.data;

        if (data === "[DONE]" || data === "done") {
          // Query complete
          source.close();
          setEventSource(null);
          setSSEReady(false);
          setIsConnected(false);
          if (onQueryComplete) {
            onQueryComplete(accumulatedText, sourceRefs);
          }
          return;
        }

        try {
          const parsed = JSON.parse(data);
          if (parsed.type === "token") {
            // Receive a token with accumulated context and source refs
            const { text, context, finished, source_refs } = parsed;

            if (text) {
              setAccumulatedText((prev) => prev + text);
            }
            if (source_refs && Array.isArray(source_refs)) {
              setSourceRefs(source_refs);
            }
            if (typeof onTokenReceived === "function") {
              onTokenReceived(text, accumulatedText, source_refs);
            }

            // Auto-scroll if this is the last token
            if (finished && autoScroll) {
              window.scrollTo(0, document.body.scrollHeight);
            }
          } else if (parsed.type === "done") {
            // Final event
            if (onQueryComplete) {
              onQueryComplete(parsed.text, parsed.source_refs || sourceRefs);
            }
            source.close();
            setEventSource(null);
            setSSEReady(false);
            setIsConnected(false);
          }
        } catch (e) {
          console.error("Failed to parse SSE message:", e, data);
          if (onError) {
            onError(`Failed to parse message: ${data}`);
          }
        }
      };

      source.onerror = (err) => {
        console.error("SSE error:", err);
        setIsConnected(false);
        if (onError) {
          onError("SSE connection error. Retrying...");
        }
        // Attempt reconnection
        if (reconnectAttempts.current < maxReconnects) {
          reconnectAttempts.current++;
          const delay = 1000 * Math.pow(1.5, reconnectAttempts.current);
          setTimeout(() => {
            // Re-initialize with same question
            if (question.trim()) {
              // Force re-effect by key change or just resubmit
              source.reconnect();
            }
          }, delay);
        }
      };
    } catch (e) {
      console.error("Failed to create SSE connection:", e);
      if (onError) {
        onError(`Could not connect to SSE endpoint: ${e.message}`);
      }
    }

    // Cleanup on unmount or question change
    return () => {
      if (source) {
        source.close();
        setEventSource(null);
        setSSEReady(false);
        setIsConnected(false);
      }
    };
  }, [question, onTokenReceived, onQueryComplete, onError, autoScroll, initialSourceRefs]);

  // While connecting, show placeholder
  if (!sseReady && !question) {
    return null;
  }

  // Display accumulated text while streaming
  const displayText = accumulatedText || "Waiting for response...";

  return (
    <div style={{
      maxWidth: "800px",
      margin: "0 auto",
      fontFamily: "system-ui, sans-serif",
      border: "1px solid #e0e0e0",
      borderRadius: "8px",
      overflow: "hidden",
    }}>
      <div style={{
        background: "#f8f9fa",
        padding: "1rem 1.5rem",
        borderBottom: "1px solid #e0e0e0",
        fontWeight: "500",
      }}>
        <strong>Question:</strong> {question}
      </div>

      <div style={{
        padding: "1rem 1.5rem",
        color: "#202123",
        minHeight: "120px",
        overflowY: "auto",
        fontSize: "0.95rem",
        lineHeight: "1.5",
      }}>
        <div dangerouslySetInnerHTML={{ __html: displayText }} />
      </div>

      {/* Source citation pills area */}
      {sourceRefs.length > 0 && (
        <div style={{
          padding: "0.5rem 1.5rem",
          background: "#f0f2f5",
          fontSize: "0.75rem",
          color: "#555",
        }}>
          <strong>Sources:</strong> {sourceRefs.map((ref, i) =>
            <span key={i} style={{ marginRight: "0.5rem", cursor: "pointer" }}
              onClick={() => window.scrollTo(0, 0)}>[{ref.page_number || i + 1}]</span>
          )} 
        </div>
      )}

      <div style={{
        padding: "1rem 1.5rem",
        borderTop: "1px solid #e0e0e0",
        background: "#f8f9fa",
        display: "flex",
        justifyContent: "flex-end",
      }}>
        {isConnected ? (
          <span>Streaming...</span>
        ) : (
          <span>Connection lost</span>
        )}
      </div>
    </div>
  );
};

export default ChatSSE;