// A delayed Firestore snapshot must not replace a clarification already returned
// by the authenticated game endpoint. Cached reviews cannot reveal new answers.
export function withCurrentReviews(progress,currentReviews={}) {
 const reviews={...(progress.reviews||{})};
 for(const [index,review] of Object.entries(currentReviews))if(progress.answers?.[index]&&review.solutionReviewVersion)reviews[index]=review;
 return {...progress,reviews};
}
