/** Query Input Component for Enterprise RAG Workspace.

Handles user question submission with SSE streaming of grounded responses.
Integrates with the ChatSSE component for live token streaming and
citation pill rendering.
*/

import React, { useState, useEffect, useRef, } from "react";
import { useHistory, useLocation } from "react-router-dom";
import ChatSSE from "./ChatSSE";

// Import API client
// import { queriesAPI } from "../services/api";

const QueryInput = ({
  workspaceId,
  onQueryComplete,     // (fullText, sourceRefs) callback
  initialSourceRefs = [], // initial citations from previous context
}) => {
  const [question, setQuestion] = useState("");
  const history = useHistory();
  const location = useLocation();
  const inputRef = useRef(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || isSubmitting) return;

    setIsSubmitting(true);
    setQuestion(""); // Clear immediately so user can type next query

    try {
      // Submit query via SSE streaming
      const { stream } = await queriesAPI.submit(
        workspaceId,
        [],  // document_ids - optional; omit to search all docs in workspace
        q,
        null   // user_id - would come from auth context
      );

      if (!stream) {
        // Non-streaming fallback
        // alert("SSE not supported, falling back to standard response");
        setIsSubmitting(false);
        return;
      }

      // Process SSE stream using the generator
      const parser = queriesAPI.parseSSE(stream);
      let finalText = "";
      let finalSourceRefs = initialSourceRefs;

      for await (const event of parser) {
        if (event.done) {
          // Query complete
          if (onQueryComplete) {
            onQueryComplete(finalText, finalSourceRefs);
          }
          break;
        }

        if (event.type === "token") {
          // Accumulate token text
          const tokenText = event.text || "";
          finalText += tokenText;

          // Update source references if provided
          if (event.source_refs && Array.isArray(event.source_refs)) {
            finalSourceRefs = event.source_refs;
          }

          // Callback for UI updates (citation pills, etc.)
          // onTokenReceived(tokenText, finalText, finalSourceRefs);
        } else if (event.raw) {
          // Raw non-JSON message
          console.log("Raw SSE event:", event.raw);
        }
      }
    } catch (err) {
      console.error("Query submission error:", err);
      // Could set error state to show to user
    } finally {
      setIsSubmitting(false);
    }
  };

  // Auto-focus input on mount
  useEffect(() => {
    if (question === "") {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  }, [question]);

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto" }}>
      <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
        <div style={{
          border: "1px solid #ddd",
          borderRadius: "20px",
          padding: "0.5rem 1rem",
          display: "flex",
          alignItems: "center",
          background: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        }}>
          <input
            ref={inputRef}
            type="text"
            placeholder="Ask a question about your documents..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isSubmitting}
            style={{
              border: "none",
              flex: 1,
              fontSize: "0.95rem",
              outline: "none",
            }}
          />
          <button
            type="submit"
            disabled={isSubmitting || !question.trim()}
            style={{
              background: "#42b983",
              color: "white",
              border: "none",
              padding: "0 1.5rem",
              borderRadius: "20px",
              fontSize: "0.9rem",
              whiteSpace: "nowrap",
            }}
          >
            {isSubmitting ? "Sending..." : "Ask"}
          </button>
        </div>
      </form>

      {/* Streamed response area - shown after submission */}
      {question.trim() && !isSubmitting && (
        <ChatSSE
          question={question}
          onTokenReceived={(tokenText, accumulatedText, sourceRefs) => {
            // Could update citation pills in real-time here
            console.log(`Token: ${tokenText}, Sources:`, sourceRefs);
          }}
          onQueryComplete={(fullText, sourceRefs)} => {
            // Query complete - full answer received with sources
            console.log("Query complete!", { fullTextLength: fullText.length, sources: sourceRefs.length });
            // Optionally auto-focus input for next question
            setQuestion("");
          }
          onError={(msg) => console.error("SSE Error:", msg)}
          initialSourceRefs={initialSourceRefs}
        />
      )}
    </div>
  );
};

export default QueryInput;