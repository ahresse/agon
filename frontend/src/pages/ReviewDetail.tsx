import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getReview, ReviewDetail as ReviewDetailType } from "../services/apiClient";
import { GradeBreakdown } from "../components/GradeBreakdown";
import { WeightEditor } from "../components/WeightEditor";

export function ReviewDetail() {
  const { reviewId } = useParams<{ reviewId: string }>();
  const [review, setReview] = useState<ReviewDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reviewId) return;
    getReview(reviewId).then(setReview).catch((e) => setError((e as Error).message));
  }, [reviewId]);

  if (error) return <p className="error">{error}</p>;
  if (!review) return <p>Loading…</p>;
  return (
    <>
      <GradeBreakdown review={review} />
      <WeightEditor review={review} onRecomputed={setReview} />
    </>
  );
}
