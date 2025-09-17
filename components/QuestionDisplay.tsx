
import React from 'react';
import { type Question } from '../types';

interface QuestionDisplayProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
}

export const QuestionDisplay: React.FC<QuestionDisplayProps> = ({ question, questionNumber, totalQuestions }) => {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <span className="bg-indigo-100 text-indigo-800 text-sm font-semibold mr-2 px-3 py-1 rounded-full dark:bg-indigo-900 dark:text-indigo-200">
          {question.subject}
        </span>
        <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Question {questionNumber} / {totalQuestions}
        </span>
      </div>
      <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 leading-snug">
        {question.text}
      </h2>
    </div>
  );
};
   