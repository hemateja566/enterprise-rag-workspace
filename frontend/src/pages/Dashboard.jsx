/** Main Dashboard / Workspace Page for Enterprise RAG Workspace.

Combines all major UI components:
- Document upload area
- Document list / viewer
- PDF viewer with citation highlighting
- Chat-style Q&A with SSE streaming
- Multi-tenant workspace isolation
*/

import React, { useState, useEffect, useRef } from "react";
import { useHistory, useLocation } from "react-router-dom";
import DocumentUpload from "../components/DocumentUpload";
import { Document as PDFDocument } from "react-pdf";
import { useDispatch } from "react-redux"; // optional - for state management
import QueryInput from "../components/QueryInput";

// Import API and models
// import { authAPI, documentsAPI, queriesAPI } from "../services/api";
import PDFViewer from "../components/PDFViewer";

const Dashboard = () => {
  const [workspaceId, setWorkspaceId] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [currentDocument, setCurrentDocument] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [showUpload, setShowUpload] = useState(false);
  const [queryHistory, setQueryHistory] = useState([]); // optional: recent queries
  const dispatch = useDispatch();
  const history = useHistory();
  const location = useLocation();

  // Extract workspace from location or auth state
  useEffect(() => {
    // In production, workspace_id would come from JWT claims or auth context
    // For now, use a default or query param
    const urlParams = new URLSearchParams(location.search);
    const savedWid = urlParams.get("workspace_id");
    if (savedWid) {
      setWorkspaceId(parseInt(savedWid, 10));
    } else {
      // No workspace selected - show upload first
      setShowUpload(true);
    }
  }, [location]);

  // Load documents for the workspace when workspaceId changes
  useEffect(() => {
    if (!workspaceId) return;
    // documentsAPI.list(workspaceId).then(res => setDocuments(res.documents));
    // Simulated load
    console.log(`Loading documents for workspace ${workspaceId}`);
  }, [workspaceId]);

  // Handle document selection
  const handleDocumentSelect = (doc) => {
    setCurrentDocument(doc);
    setCurrentPage(1);
    setShowUpload(false);
  };

  // Handle page change from PDF viewer or citation click
  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Handle citation/highlight click - scroll to exact location
  const handleHighlightClick = (pageNumber, coords) => {
    setCurrentPage(pageNumber);
    // In a full implementation, we'd scroll to specific paragraph/coordinates
    // window.scrollTo({ top: coords.top, behavior: "smooth" });
    console.log(`Citation clicked: Page ${pageNumber}, coords:`, coords);
  };

  // Handle query completion with sources
  const handleQueryComplete = (fullText, sourceRefs) => {
    console.log("Query complete, sources:", sourceRefs.length);
    setQueryHistory((prev) => [
      ...prev,
      { question: "Latest query", answer: fullText.substring(0, 100) + "...", sources: sourceRefs.length },
    ].slice(0, 10)); // Keep last 10
  };

  // If no workspace, show upload area
  if (showUpload) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", minHeight: "80vh" }}>
        <h2>Enterprise RAG Workspace</h2>
        <p>Select or create a workspace to begin document analysis.</p>

        <DocumentUpload
          workspaceId={workspaceId || 0}
          onUploadComplete={(doc) => handleDocumentSelect(doc)}
        />
      </div>
    );
  }

  // Main workspace layout
  return (
    <div style={{ minHeight: "800px", background: "#fafafa" }}>
      <header style={{
        background: "white",
        padding: "1rem 2rem",
        borderBottom: "1px solid #eee",
        margin: "-1rem -1rem 2rem -1rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <h1 style={{ margin: 0, fontSize: "1.5rem" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" style={{ marginRight: "0.5rem", color: "#42b983" }}>
            <path d="M3 5a2 2 0 012-2h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5zM9 10h6v2H9v-2zm3 3h2v2h-2v-2zm-3-8h2v6H6V9z" fill="#555" />
          </svg>
          Research Workspace
        </h1>
        <div>
          {/* User profile/avatar would go here */}
          <span style={{ marginLeft: "1rem", fontSize: "0.8rem", color: "#666" }}>
            WS-{workspaceId || "—"}
          </span>
        </div>
      </header>

      <div style={{ display: "flex", height: "700px" }}>
        {/* LEFT PANEL: Document List & Controls */}
        <div style={{ width: "220px", flexShrink: 0, background: "white", borderRight: "1px solid #eee" }}>
          <div style={{ padding: "1rem" }}>
            <h4 style={{ margin: "0 0 1rem 0", fontSize: "0.9rem" }}>Documents</h4>

            {workspaceId && (
              <div style={{ height: "300px", overflowY: "auto" }}>
                {documents.length === 0 ? (
                  <p style={{ padding: "1rem", color: "#666" }}>No documents in this workspace.</p>
                ) : (
                  documents.map((doc) => (
                    <div
                      key={doc.id}
                      style={{
                        padding: "0.5rem",
                        borderBottom: "1px solid #f0f0f0",
                        fontSize: "0.8rem",
                        cursor: "pointer",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                      onClick={() => handleDocumentSelect(doc)}
                    >
                      {doc.original_filename || `Doc ${doc.id}`}
                      {doc.status === "ready" && (
                        <span style={{ float: "right", fontSize: "0.7rem", color: "#42b983" }}>
                          Ready
                        </span>
                      )}
                      {doc.status === "processing" && (
                        <span style={{ float: "right", fontSize: "0.7rem", color: "#f6e05e" }}>
                          Processing
                        </span>
                      )}
                    </div>
                  ))
                )}
              </div>
            })

            {/* Upload button */}
            <button
              style={{
                width: "100%",
                marginTop: "1rem",
                padding: "0.5rem",
                textAlign: "left",
                background: "transparent",
                border: "1px solid #42b983",
                color: "#42b983",
                borderRadius: "4px",
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
              onClick={() => setShowUpload(true)}
            >
              + Upload Document
            </button>
          </div>
        </div>

        {/* RIGHT PANEL: Document Viewer + Chat */}
        <div style={{ flexGrow: 1, background: "#fff", overflow: "hidden" }}>
          {/* Document Viewer Area */}
          {currentDocument ? (
            <PDFViewer
              filePath={currentDocument.stored_path}
              initialPage={currentPage}
              onPageChange={handlePageChange}
              onHighlightClick={handleHighlightClick}
              showCitations={true}
            />
          ) : (
            <div style={{
              padding: "2rem",
              color: "#666",
              textAlign: "center",
            }}>
              <h3>Select a document to view</h3>
              <p>Upload a PDF or choose from existing documents in the left panel.</p>
            </div>
          )}

          {/* Chat / Query Area - bottom of right panel */}
          <div style={{
            padding: "1rem 2rem",
            borderTop: "1px solid #eee",
            background: "#f8f9fa",
          }}>
            <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem" }}>
              Ask a question
            </h4>
            <QueryInput
              workspaceId={workspaceId}
              onQueryComplete={handleQueryComplete}
              initialSourceRefs={[]}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;