
import React, { useState, useCallback } from 'react';
import { QuestionDisplay } from './components/QuestionDisplay';
import { AnswerInput } from './components/AnswerInput';
import { GradingResultDisplay } from './components/GradingResultDisplay';
import { LoadingSpinner } from './components/LoadingSpinner';
import { Header } from './components/Header';
import { ErrorDisplay } from './components/ErrorDisplay';
import { gradeAnswer } from './services/geminiService';
import { QUESTIONS } from './constants';
import { type Question, type GradingResult } from './types';

export default function App() {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [gradingResult, setGradingResult] = useState<GradingResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion: Question = QUESTIONS[currentQuestionIndex];

  const handleGrade = useCallback(async () => {
    if (!userAnswer.trim()) {
      setError("回答を入力してください。");
      return;
    }
    if (userAnswer.length > 100) {
      setError("回答は100文字以内で入力してください。");
      return;
    }
    setIsLoading(true);
    setError(null);
    setGradingResult(null);

    try {
      const result = await gradeAnswer(currentQuestion, userAnswer);
      setGradingResult(result);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "An unknown error occurred during grading.");
    } finally {
      setIsLoading(false);
    }
  }, [userAnswer, currentQuestion]);

  const handleNextQuestion = () => {
    setUserAnswer('');
    setGradingResult(null);
    setError(null);
    setCurrentQuestionIndex((prevIndex) => (prevIndex + 1) % QUESTIONS.length);
  };

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-200 font-sans">
      <Header />
      <main className="container mx-auto p-4 md:p-8 max-w-4xl">
        <div className="bg-white dark:bg-slate-800 shadow-2xl rounded-2xl p-6 md:p-8 space-y-8">
          <QuestionDisplay
            question={currentQuestion}
            questionNumber={currentQuestionIndex + 1}
            totalQuestions={QUESTIONS.length}
          />

          <AnswerInput
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            onSubmit={handleGrade}
            isLoading={isLoading}
            isGraded={!!gradingResult}
          />
          
          {isLoading && <LoadingSpinner />}
          {error && <ErrorDisplay message={error} />}

          {gradingResult && (
            <div className="animate-fade-in">
              <GradingResultDisplay result={gradingResult} />
              <div className="mt-8 text-center">
                <button
                  onClick={handleNextQuestion}
                  className="px-8 py-3 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-300 dark:focus:ring-indigo-800 transition-all duration-300 ease-in-out transform hover:scale-105"
                >
                  Next Question &rarr;
                </button>
              </div>
            </div>
          )}
        </div>
        <footer className="text-center mt-8 text-slate-500 dark:text-slate-400 text-sm">
            <p>Powered by Google Gemini</p>
        </footer>
      </main>
    </div>
  );
}
