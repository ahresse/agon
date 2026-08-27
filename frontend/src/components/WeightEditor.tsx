import { useState } from "react";
import {
  ReviewDetail as ReviewDetailType,
  updateWeights,
  WeightOverride,
} from "../services/apiClient";

interface Props {
  review: ReviewDetailType;
  onRecomputed: (updated: ReviewDetailType) => void;
}

/**
 * Per-review weight editor (US2, FR-009/010). Editing a weight recomputes the
 * final grade instantly from stored results without re-running any test.
 */
export function WeightEditor({ review, onRecomputed }: Props) {
  const [weights, setWeights] = useState<Record<string, number>>(
    Object.fromEntries(review.results.map((r) => [r.test_id, r.effective_weight])),
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const apply = async () => {
    setSaving(true);
    setError(null);
    const overrides: WeightOverride[] = Object.entries(weights).map(([test_id, weight]) => ({
      test_id,
      weight,
    }));
    try {
      const updated = await updateWeights(review.id, overrides);
      onRecomputed(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="weight-editor">
      <h3>Adjust weights</h3>
      {error && <p className="error">{error}</p>}
      <table>
        <tbody>
          {review.results.map((r) => (
            <tr key={r.test_id}>
              <td>{r.test_name}</td>
              <td>
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  value={weights[r.test_id]}
                  aria-label={`weight-${r.test_name}`}
                  onChange={(e) =>
                    setWeights({ ...weights, [r.test_id]: Number(e.target.value) })
                  }
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button onClick={apply} disabled={saving}>
        {saving ? "Recomputing…" : "Apply & re-grade"}
      </button>
    </section>
  );
}
