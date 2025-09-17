
export interface Question {
  id: number;
  subject: string;
  text: string;
  modelAnswer: string;
}

export interface RubricItem {
  criterion: string;
  score: number;
  maxScore: number;
  feedback: string;
}

export interface GradingResult {
  rubricScores: RubricItem[];
  similarityScore: number;
  overallScore: number;
  overallFeedback: string;
}
   