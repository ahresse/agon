import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listReviews, ReviewSummary } from "../services/apiClient";

/** History view (US4, FR-011): lists prior reviews and links to their detail. */
export function History() {
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listReviews().then(setReviews).catch((e) => setError((e as Error).message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  return (
    <section className="history">
      <h2>Review history</h2>
      {reviews.length === 0 ? (
        <p>No reviews yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Date</th>
              <th>Status</th>
              <th>Final grade</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((r) => (
              <tr key={r.id}>
                <td>{r.candidate_label}</td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>{r.status}</td>
                <td>{r.final_grade ?? "—"}</td>
                <td>
                  <Link to={`/reviews/${r.id}`}>Open</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
