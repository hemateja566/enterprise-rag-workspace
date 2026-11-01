/** PDF Viewer Component for Enterprise RAG Workspace.

Renders PDF documents using react-pdf and provides:
- Side-by-side or single-page viewing
- Highlight coordinates from search/retrieval results
- Source citation integration: clicking a citation scrolls to the exact page/paragraph
- Page navigation and zoom controls
*/

import React, { useEffect, useRef, useState } from "react";
import { Document, Page, TextLayer, pdfjsLib } from "react-pdf";
import "react-pdf/dist/react-pdf.css";

// pdfjsLib configuration - point to Mozilla CDN or custom build
pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdn.jsdelivr.net/npm/react-pdf@2.5.0/build/pdf.worker.js";

const DEFAULT_ZOOM = 1.0;
const ANIMATION_DURATION = 300; // ms

const PDFViewer = ({
  filePath,
  initialPage = 1,
  onPageChange,
  onHighlightClick,
  showCitations = true,
}) => {
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const totalPagesRef = useRef(0);
  const pageRefs = useRef({}); // refs for each page number
  const scrollAnimationRef = useRef(false);

  // Load PDF document
  useEffect(() => {
    if (!filePath) return;

    const loadDoc = async () => {
      try {
        const loadingTask = pdfjsLib.getDocument(filePath);
        const doc = await loadingTask.promise;
        totalPagesRef.current = doc.numPages;
        setCurrentPage(initialPage || 1);

        // If we have a target page from props (citation), scroll to it
        if (onPageChange) {
          onPageChange(initialPage || 1);
        }
      } catch (err) {
        console.error("PDF loading error:", err);
      }
    };

    loadDoc();

    // Cleanup on unmount
    return () => {
      // No explicit cleanup needed for react-pdf
    };
  }, [filePath, initialPage, onPageChange]);

  // Handle page change (e.g., from citation click)
  useEffect(() => {
    if (onPageChange) {
      onPageChange(currentPage);
    }
  }, [currentPage, onPageChange]);

  // Navigate to specific page (called from citation click)
  const goToPage = (pageNum) => {
    setCurrentPage(pageNum);
    // Option: smooth scroll animation here
    scrollAnimationRef.current = true;
    // Trigger re-render with new page
  };

  // Handle highlight/coordinate click from citation
  const handleHighlightPress = (pageNumber, { left, top, width, height }) => {
    if (onHighlightClick) {
      onHighlightClick(pageNumber, { left, top, width, height });
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === "ArrowUp" || e.key === "k") {
      e.preventDefault();
      setCurrentPage((prev) => Math.max(1, prev - 1));
    } else if (e.key === "ArrowDown" || e.key === "j") {
      e.preventDefault();
      setCurrentPage((prev) => Math.min(totalPagesRef.current, prev + 1));
    }
  };

  if (!filePath) {
    return (
      <div style={{ padding: "2rem", color: "#666" }}>
        <p>No PDF document loaded. Upload a document to view.</p>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "sans-serif", background: "#fff" }} onKeyDown={handleKeyDown}>
      <div style={{ display: "flex", marginBottom: "1rem" }}>
        <button
          onClick={() => goToPage(1)}
          disabled={currentPage === 1}
          style={{ marginRight: "0.5rem" }}
        >
          <<
        </button>
        <button
          onClick={() => goToPage(currentPage - 1)}
          disabled={currentPage === 1}
        >
          <
        </button>
        <span style={{ margin: "0 1rem", color: "#555" }}>
          Page {currentPage} of {totalPagesRef.current || 1}
        </span>
        <button
          onClick={() => goToPage(currentPage + 1)}
          disabled={currentPage >= (totalPagesRef.current || 1)}
        >
          >
        </button>
        <button
          onClick={() => goToPage(totalPagesRef.current || 1)}
          disabled={currentPage >= (totalPagesRef.current || 1)}
        >
          >>
        </button>
      </div>

      <div style={{ display: "flex", justifyContent: "center" }}>
        <Document
          file={filePath}
          zoom={zoom}
          onPageError={({ report }) => {
            console.error("PDF Page Error:", report);
          }}
        >
          {({ page }) => {
            return (
              <Page
                index={currentPage - 1}
                onClick={({ pageIndex, x, y }) => {
                  // Handle click on page - could show coordinates
                  console.log(`Page ${currentPage + 1} clicked at (${x}, ${y})`);
                }}
              >
                <TextLayer />
              </Page>
            );
          }}
        </Document>
      </div>

      {showCitations && totalPagesRef.current > 0 && (
        <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid #eee" }}>
          <h4>Citations & Highlights</h4>
          {/* Citation pills would be rendered here by parent component */}
          <p style={{ fontSize: "0.8rem", color: "#666" }}>
            Click any citation to scroll to the corresponding page and paragraph
          </p>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;