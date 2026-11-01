#!/usr/bin/env javascript
/** API Client for Enterprise RAG Workspace Frontend.

Provides functions to communicate with the Flask backend:
- Authentication (login/register/me/refresh)
- Document management (upload, list, delete)
- Query submission with SSE streaming
- SSE event handling for streaming token responses
*/

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";

// Helper: add auth header if token available
function getAuthHeaders() => {
  const token = typeof window !== "undefined" ? localStorage.getItem("jwt_token") : null;
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

/** Auth API */
export const authAPI = {
  login: async (email, password) => {
    const resp = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await resp.json();
    if (data.access_token) {
      localStorage.setItem("jwt_token", data.access_token);
    }
    return data;
  },

  register: async (email, password, fullName) => {
    const resp = await fetch(`${BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    return resp.json();
  },

  me: async () => {
    const resp = await fetch(`${BASE_URL}/auth/me`, {
      headers: getAuthHeaders(),
    });
    return resp.json();
  },

  refresh: async () => {
    const resp = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: localStorage.getItem("refresh_token") }),
    });
    const data = await resp.json();
    if (data.access_token) {
      localStorage.setItem("jwt_token", data.access_token);
    }
    return data;
  },
};

/** Document API */
export const documentsAPI = {
  list: async (workspaceId) => {
    const resp = await fetch(`${BASE_URL}/documents?workspace_id=${workspaceId}`, {
      headers: getAuthHeaders(),
    });
    return resp.json();
  },

  upload: async (workspaceId, file) => {
    const formData = new FormData();
    formData.append("workspace_id", workspaceId);
    formData.append("file", file);

    const resp = await fetch(`${BASE_URL}/documents/upload`, {
      method: "POST",
      body: formData,
      headers: getAuthHeaders(), // Do NOT set Content-Type; browser sets multipart
    });
    return resp.json();
  },

  get: async (documentId) => {
    const resp = await fetch(`${BASE_URL}/documents/${documentId}`, {
      headers: getAuthHeaders(),
    });
    return resp.json();
  },

  delete: async (documentId) => {
    const resp = await fetch(`${BASE_URL}/documents/${documentId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    return resp.json();
  },
};

/** Query API with SSE streaming */
export const queriesAPI = {
  submit: async (workspaceId, documentIds, question, userId) => {
    const resp = await fetch(`${BASE_URL}/queries/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        workspace_id: workspaceId,
        document_ids: documentIds || [],
        question,
        user_id: userId,
      }),
      // NOTE: For SSE, we cannot use the default JSON body parsing that
      // creates the response. The Flask route returns a Response(streaming).
      // The browser will interpret the stream as text/event-stream.
    });

    if (!resp.body || !resp.headers.get("content-type") || !resp.headers.get("content-type").includes("text/event-stream")) {
      // Fallback: non-streaming response
      const data = await resp.json();
      return { stream: null, data };
    }

    // Return the readable stream for SSE processing
    return { stream: resp.stream(), data: null };
  },

  /** Parse SSE stream and yield events */
  *parseSSE(stream) {
    const reader = stream.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Split by event lines
      const lines = buffer.split("\n");
      // Keep unfinished last line in buffer
      buffer = lines.pop().trim(); // last element might be incomplete

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const payload = line.slice("data: ".length).trim();
          if (payload === "[DONE]") {
            yield { done: true };
            return;
          }
          try {
            yield JSON.parse(payload);
          } catch (e) {
            yield { raw: payload };
          }
        }
      }
    }
  },
};