import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { WeightEditor } from "../src/components/WeightEditor";
import type { ReviewDetail } from "../src/services/apiClient";
import * as api from "../src/services/apiClient";

const review: ReviewDetail = {
  id: "r1",
  submission_id: "s1",
  reviewer_id: "u1",
  status: "COMPLETED",
  final_grade: 80,
  candidate_label: "Alice",
  created_at: "2026-08-26T00:00:00Z",
  results: [
    {
      test_id: "t1",
      test_name: "Lint (ruff)",
      grade: 90,
      status: "SUCCESS",
      effective_weight: 1,
      contribution: 45,
      pros: [],
      cons: [],
    },
  ],
  pros: [],
  cons: [],
};

describe("WeightEditor", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("renders a weight input per test", () => {
    render(<WeightEditor review={review} onRecomputed={() => {}} />);
    expect(screen.getByLabelText("weight-Lint (ruff)")).toBeDefined();
  });

  it("recomputes and invokes callback on apply", async () => {
    const updated = { ...review, final_grade: 95 };
    const spy = vi.spyOn(api, "updateWeights").mockResolvedValue(updated);
    const onRecomputed = vi.fn();
    render(<WeightEditor review={review} onRecomputed={onRecomputed} />);

    fireEvent.change(screen.getByLabelText("weight-Lint (ruff)"), { target: { value: "5" } });
    fireEvent.click(screen.getByText(/Apply & re-grade/));

    await waitFor(() => expect(onRecomputed).toHaveBeenCalledWith(updated));
    expect(spy).toHaveBeenCalledWith("r1", [{ test_id: "t1", weight: 5 }]);
  });
});
