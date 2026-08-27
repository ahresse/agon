import type { ReviewDetail } from "../services/apiClient";

export function GradeBreakdown({ review }: { review: ReviewDetail }) {
  return (
    <div className="grade-breakdown">
      <h2>
        Final Grade: {review.final_grade !== null ? review.final_grade.toFixed(1) : "—"} / 100
      </h2>
      <p>
        Candidate: <strong>{review.candidate_label}</strong> · Status: {review.status}
      </p>

      <table>
        <thead>
          <tr>
            <th>Test</th>
            <th>Grade</th>
            <th>Weight</th>
            <th>Contribution</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {review.results.map((r) => (
            <tr key={r.test_id} className={r.status === "FAILED" ? "failed" : ""}>
              <td>{r.test_name}</td>
              <td>{r.grade.toFixed(1)}</td>
              <td>{r.effective_weight}</td>
              <td>{r.contribution.toFixed(1)}</td>
              <td>{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pros-cons">
        <div>
          <h3>Pros</h3>
          <ul>
            {review.pros.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Cons</h3>
          <ul>
            {review.cons.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
