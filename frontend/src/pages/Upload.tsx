import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadSubmission } from "../services/apiClient";

export function Upload() {
  const [candidateLabel, setCandidateLabel] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!file) {
      setError("Please choose a submission archive.");
      return;
    }
    setBusy(true);
    try {
      const review = await uploadSubmission(candidateLabel, file);
      navigate(`/reviews/${review.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="upload">
      <h1>New Assessment</h1>
      <label>
        Candidate label
        <input
          value={candidateLabel}
          onChange={(e) => setCandidateLabel(e.target.value)}
          required
        />
      </label>
      <label>
        Submission archive (.zip or .tar.gz of Python code)
        <input
          type="file"
          accept=".zip,.tar.gz,.tgz,.tar,application/zip,application/gzip"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={busy}>
        {busy ? "Assessing…" : "Upload & Assess"}
      </button>
    </form>
  );
}
