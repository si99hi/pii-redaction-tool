import React, { useState } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [piiSummary, setPiiSummary] = useState(null);
  const [redactedBlob, setRedactedBlob] = useState(null);
  const [redactedFileName, setRedactedFileName] = useState('');

  const handleFileChange = (e) => {
    setError('');
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.docx')) {
        setError('Only Microsoft Word (.docx) files are supported.');
        setFile(null);
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleRedact = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setSuccess(false);
    setPiiSummary(null);
    setRedactedBlob(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${BACKEND_URL}/redact`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || 'An error occurred during redaction.');
      }

      const piiHeader = response.headers.get('X-Detected-PII');
      if (piiHeader) {
        try {
          setPiiSummary(JSON.parse(piiHeader));
        } catch (e) {
          console.error('Failed to parse PII header', e);
        }
      }

      const blob = await response.blob();
      setRedactedBlob(blob);
      setRedactedFileName(`redacted_${file.name}`);
      setSuccess(true);
    } catch (err) {
      const msg = err.message || '';
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('network error') || msg === 'TypeError: Failed to fetch') {
        setError('Could not connect to the backend server. If the server is starting up, please wait 1-5 minutes for the server to wake and try again.');
      } else {
        setError(msg || 'Failed to communicate with the backend server.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!redactedBlob) return;
    const url = window.URL.createObjectURL(redactedBlob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', redactedFileName);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
  };

  const handleReset = () => {
    setFile(null);
    setSuccess(false);
    setError('');
    setPiiSummary(null);
    setRedactedBlob(null);
    setRedactedFileName('');
  };

  return (
    <div className="app-container">
      <style>{`
        /* Claude-inspired layout with strictly sharp edges and high contrast */
        .app-container {
          max-width: 650px;
          margin: 60px auto;
          padding: 40px;
          background: #ffffff;
          border: 1px solid #e5e0da;
        }

        header {
          margin-bottom: 30px;
          border-bottom: 1px solid #e5e0da;
          padding-bottom: 20px;
        }

        h1 {
          font-size: 2.2rem;
          margin-bottom: 8px;
          letter-spacing: -0.5px;
        }

        .subtitle {
          color: #5e5650;
          font-size: 0.95rem;
        }

        .upload-section {
          margin-bottom: 24px;
        }

        /* Sharp bordered drag & drop style zone */
        .file-dropzone {
          border: 2px dashed #d5cfc8;
          background: #faf8f5;
          padding: 40px 20px;
          text-align: center;
          cursor: pointer;
          transition: background 0.15s ease, border-color 0.15s ease;
        }

        .file-dropzone:hover {
          background: #f5f2ed;
          border-color: #1d1916;
        }

        .file-input {
          display: none;
        }

        .filename-box {
          margin-top: 15px;
          padding: 12px;
          background: #faf8f5;
          border: 1px solid #e5e0da;
          font-family: monospace;
          font-size: 0.9rem;
          text-align: left;
          color: #1d1916;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .btn-remove {
          background: none;
          border: none;
          color: #a32a2a;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.85rem;
        }

        .btn-remove:hover {
          text-decoration: underline;
        }

        /* All buttons strictly sharp-edged (border-radius: 0) */
        .btn {
          background: #1d1916;
          color: #ffffff;
          border: none;
          padding: 14px 20px;
          font-family: inherit;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          width: 100%;
          display: block;
          text-align: center;
          transition: background 0.15s ease;
        }

        .btn:hover {
          background: #403c37;
        }

        .btn:disabled {
          background: #cccccc;
          cursor: not-allowed;
        }

        .btn-download {
          background: #1c4d25;
        }

        .btn-download:hover {
          background: #2e6939;
        }

        .btn-secondary {
          background: transparent;
          color: #1d1916;
          border: 1px solid #1d1916;
          margin-top: 12px;
        }

        .btn-secondary:hover {
          background: #faf8f5;
        }

        /* Alerts and loaders with sharp edges */
        .loader {
          text-align: center;
          padding: 24px 20px;
          background: #faf8f5;
          border: 1px solid #e5e0da;
          color: #1d1916;
          font-family: monospace;
          margin-bottom: 20px;
        }

        .progress-bar-container {
          width: 100%;
          height: 6px;
          background-color: #e5e0da;
          margin-top: 16px;
          position: relative;
          overflow: hidden;
        }

        .progress-bar-fill {
          height: 100%;
          background-color: #1d1916;
          width: 35%;
          position: absolute;
          animation: slide 1.6s infinite ease-in-out;
        }

        @keyframes slide {
          0% { left: -35%; }
          100% { left: 100%; }
        }

        .error-box {
          background: #fdf2f2;
          border: 1px solid #a32a2a;
          color: #a32a2a;
          padding: 15px;
          margin-bottom: 24px;
          font-size: 0.9rem;
        }

        .success-box {
          background: #f2f7f3;
          border: 1px solid #1c4d25;
          color: #1c4d25;
          padding: 15px;
          margin-bottom: 24px;
          font-size: 0.95rem;
        }

        /* Table design with sharp edges */
        .summary-title {
          font-size: 1.25rem;
          margin: 25px 0 12px 0;
          border-bottom: 1px solid #e5e0da;
          padding-bottom: 6px;
        }

        .summary-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 24px;
        }

        .summary-table th, .summary-table td {
          border: 1px solid #e5e0da;
          padding: 10px 12px;
          text-align: left;
        }

        .summary-table th {
          background: #faf8f5;
          font-weight: 600;
          font-size: 0.9rem;
          color: #5e5650;
        }

        .summary-table td {
          font-family: monospace;
          font-size: 0.9rem;
        }

        .summary-table tr:nth-child(even) {
          background: #faf8f5;
        }
      `}</style>

      <header>
        <h1>PII Redaction Tool</h1>
        <p className="subtitle">
          Upload a Microsoft Word (.docx) prospectus to automatically detect and consistently replace PII with realistic fake values.
        </p>
      </header>

      {error && <div className="error-box">{error}</div>}

      {!success && !loading && (
        <div className="upload-section">
          <label htmlFor="file-upload" className="file-dropzone-label">
            <div className="file-dropzone">
              <strong>Click to upload</strong> or drag a DOCX file here
              <input
                id="file-upload"
                type="file"
                className="file-input"
                accept=".docx"
                onChange={handleFileChange}
              />
            </div>
          </label>

          {file && (
            <div className="filename-box">
              <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              <button className="btn-remove" onClick={handleReset}>
                Remove
              </button>
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="loader">
          <div style={{ fontWeight: 'bold' }}>
            [PROCESSING] Redacting document and generating fake values...
          </div>
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: '#5e5650' }}>
            Please wait 5-10 minutes for large documents.
          </div>
          <div className="progress-bar-container">
            <div className="progress-bar-fill"></div>
          </div>
        </div>
      )}

      {!loading && file && !success && (
        <button className="btn" onClick={handleRedact}>
          Redact Document
        </button>
      )}

      {success && (
        <div className="success-section">
          <div className="success-box">
            <strong>Success:</strong> Redaction completed. All detected PII has been consistently replaced with fake values.
          </div>

          <h3 className="summary-title">Detected PII Summary</h3>
          {piiSummary && Object.keys(piiSummary).length > 0 ? (
            <table className="summary-table">
              <thead>
                <tr>
                  <th>PII Category</th>
                  <th>Detected Entities</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(piiSummary).map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ marginBottom: '24px', color: '#5e5650', fontSize: '0.9rem' }}>
              No PII entities were detected in this document.
            </p>
          )}

          <button className="btn btn-download" onClick={handleDownload}>
            Download Redacted Document
          </button>

          <button className="btn btn-secondary" onClick={handleReset}>
            Upload Another Document
          </button>
        </div>
      )}
    </div>
  );
}
