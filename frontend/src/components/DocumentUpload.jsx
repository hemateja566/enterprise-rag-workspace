/** Document Upload Component for Enterprise RAG Workspace.

Features:
- Drag-and-drop or browse file selection
- Multi-tenant workspace selection
- Upload progress tracking
- Status display (uploaded → processing → ready → error)
- Cancel/remove upload functionality
*/

import React, { useState, useEffect, useRef, } from "react";
import { useHistory, useLocation } from "react-router-dom";

// Import API client
// import { documentsAPI } from "../services/api";

const DocumentUpload = ({ workspaceId, onUploadComplete }) => {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("idle"); // idle | uploading | success | error
  const [progress, setProgress] = useState(0);
  const history = useHistory();
  const location = useLocation();
  const inputRef = useRef(null);

  // Handle file selection via browse
  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setUploadStatus("selected");
      // Reset input ref to allow same file re-selection
      inputRef.current.value = "";
    }
  };

  // Drag-and-drop handlers
  const dragRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.effectAllowed = "copy";
    if (dragRef.current) {
      dragRef.current.style.borderColor = "#42b983";
      dragRef.current.style.backgroundColor = "#e6f7ee";
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    if (dragRef.current) {
      dragRef.current.style.borderColor = "#ddd";
      dragRef.current.style.backgroundColor = "#fff";
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (dragRef.current) {
      dragRef.current.style.borderColor = "#ddd";
      dragRef.current.style.backgroundColor = "#fff";
    }
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      setFile(dropped);
      setUploadStatus("selected");
    }
  };

  // Upload processing - simulate progress (in production, use SSE or progress events)
  const uploadDocument = async () => {
    if (!file) return;

    setUploadStatus("uploading");
    setProgress(0);

    // Simulate upload progress - in production, this would be driven by
    # Upload progress from Flask/SSE or iframe messaging
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 99) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 300);

    try {
      // Use FormData for file upload
      const formData = new FormData();
      formData.append("workspace_id", workspaceId);
      formData.append("file", file);

      const resp = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
        // Important: Do NOT set Content-Type header for multipart/form-data
        // headers: { "Content-Type": "multipart/form-data" } // DO NOT SET
      });

      clearInterval(interval);
      const result = await resp.json();

      if (resp.ok && result.document) {
        setUploadStatus("success");
        if (onUploadComplete) {
          onUploadComplete(result.document);
        }
        // Auto-redirect after short delay
        setTimeout(() => {
          history.push(`${location.pathname}`);
        }, 2000);
      } else {
        setUploadStatus("error");
        alert(result.error || "Upload failed");
      }
    } catch (err) {
      clearInterval(interval);
      setUploadStatus("error");
      console.error("Upload error:", err);
      alert("Upload failed. See console for details.");
    }
  };

  // Cancel upload
  const cancelUpload = () => {
    setFile(null);
    setUploadStatus("idle");
    setProgress(0);
  };

  // Display
  if (uploadStatus === "idle" && !file) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#666" }}>
        <h3>Upload Document</h3>
        <p>Upload PDFs, Word docs, or spreadsheets to analyze.</p>

        <div style={{ margin: "1rem 0", border: "1px dashed #ddd", padding: "2rem", cursor: "pointer" }}
          onClick={() => inputRef.current && inputRef.current.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div style={{ marginBottom: "0.5rem" }}>
            <svg
              width="48" height="48" viewBox="0 0 24 24" style={{ margin: "0 auto", color: "#888" }}
            >
              <path d="M19 13h-6v6h-2v6h6v-2h-2v-6h6v-2h-2V8h2v6z" fill="#888" />
              <path d="M13 23c2.76 0 5-2.24 5-5h-2v-6h2c0 4.58 -2.34 8.33 -5 9.67z" fill="#888" />
              <path d="M12 5c-2.76 0-5 2.24-5 5h2V3.5c0-1.38 1.09-2.5 2.5-2.5s2.5 1.12 2.5 2.5H12z" fill="#888" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: "1rem", margin: "0.5rem 0" }}>Drag PDF here or</p>
            <p>Browse files</p>
          </div>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf, .doc, .docx, .xls, .xlsx"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
      </div>
    );
  }

  if (uploadStatus === "uploading") {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <h3>Uploading Document</h3>
        <p>Processing your file...</p>
        <div style={{ width: "50%", margin: "1rem auto" }}>
          <div
            style={{
              background: "#eee",
              borderRadius: "4px",
              overflow: "hidden",
              marginBottom: "0.5rem",
            }}
          >
            <div
              style={{
                width: `${progress}%`,
                background: "#42b983",
                height: "8px",
                transition: "width 0.3s ease",
              }}
            ></div>
          </div>
          <p style={{ margin: "0.5rem 0" }}>
            {progress}% {progress > 0 && progress < 100 && "Processing..."}
          </p>
        </div>
        <p>Please wait. This may take a moment for PDF parsing.</p>
        <button onClick={cancelUpload} style={{ marginTop: "0.5rem" }}>
          Cancel
        </button>
      </div>
    );
  }

  if (uploadStatus === "success") {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#2e7d32" }}>
        <h3>✓ Document Uploaded Successfully</h3>
        <p>Your document is being processed in the background.</p>
        <p>You can start querying immediately, and full analysis will complete shortly.</p>
        <button onClick={() => history.push(`${location.pathname}`)}>
          Continue to Workspace
        </button>
      </div>
    );
  }

  if (uploadStatus === "error") {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#d32f2f" }}>
        <h3>✗ Upload Failed</h3>
        <p>There was an error uploading your document.</p>
        <p>Please check the file format and try again.</p>
        <button onClick={cancelUpload}>Try Again</button>
      </div>
    );
  }

  return null;
};

export default DocumentUpload;