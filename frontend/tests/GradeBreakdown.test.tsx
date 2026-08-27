import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GradeBreakdown } from "../src/components/GradeBreakdown";
import type { ReviewDetail } from "../src/services/apiClient";

const review: ReviewDetail = {
  id: "r1",
  submission_id: "s1",
  reviewer_id: "u1",
  status: "COMPLETED",
  final_grade: 82.5,
  candidate_label: "Alice",
  created_at: "2026-08-26T00:00:00Z",
  results: [
    {
      test_id: "t1",
      test_name: "Readability Metric",
      grade: 90,
      status: "SUCCESS",
      effective_weight: 2,
      contribution: 60,
      pros: ["Well documented"],
      cons: [],
    },
    {
      test_id: "t2",
      test_name: "Failing Test",
      grade: 0,
      status: "FAILED",
      effective_weight: 1,
      contribution: 0,
      pros: [],
      cons: ["Test failed to complete"],
    },
  ],
  pros: ["Well documented"],
  cons: ["Test failed to complete"],
};

describe("GradeBreakdown", () => {
  it("shows the final grade and per-test breakdown", () => {
    render(<GradeBreakdown review={review} />);
    expect(screen.getByText(/Final Grade: 82.5/)).toBeDefined();
    expect(screen.getByText("Readability Metric")).toBeDefined();
    expect(screen.getByText("Well documented")).toBeDefined();
    expect(screen.getByText("Test failed to complete")).toBeDefined();
  });
});
