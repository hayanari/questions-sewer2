
import React from 'react';
import { type GradingResult, type RubricItem } from '../types';
import { CheckCircleIcon, DocumentTextIcon, LightBulbIcon } from './icons';

interface ScoreCircleProps {
    score: number;
}

const ScoreCircle: React.FC<ScoreCircleProps> = ({ score }) => {
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (score / 100) * circumference;
    const colorClass = score >= 80 ? 'text-green-500' : score >= 60 ? 'text-yellow-500' : 'text-red-500';

    return (
        <div className="relative flex items-center justify-center w-32 h-32">
            <svg className="absolute w-full h-full" viewBox="0 0 100 100">
                <circle
                    className="text-slate-200 dark:text-slate-700"
                    stroke="currentColor"
                    strokeWidth="10"
                    cx="50"
                    cy="50"
                    r="45"
                    fill="transparent"
                />
                <circle
                    className={`transform -rotate-90 origin-center ${colorClass} transition-all duration-1000 ease-out`}
                    stroke="currentColor"
                    strokeWidth="10"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    cx="50"
                    cy="50"
                    r="45"
                    fill="transparent"
                    strokeLinecap="round"
                />
            </svg>
            <span className={`text-3xl font-bold ${colorClass}`}>{score}</span>
            <span className="absolute bottom-6 text-xs font-medium text-slate-500 dark:text-slate-400">/ 100</span>
        </div>
    );
};

const RubricItemDisplay: React.FC<{ item: RubricItem }> = ({ item }) => (
    <div className="p-4 bg-slate-100 dark:bg-slate-700/50 rounded-lg">
        <div className="flex justify-between items-center mb-2">
            <h4 className="font-semibold text-slate-700 dark:text-slate-200">{item.criterion}</h4>
            <span className="font-bold text-lg text-indigo-600 dark:text-indigo-400">{item.score} <span className="text-sm font-normal text-slate-500 dark:text-slate-400">/ {item.maxScore}</span></span>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-300">{item.feedback}</p>
    </div>
);


export const GradingResultDisplay: React.FC<{ result: GradingResult }> = ({ result }) => {
  return (
    <div className="space-y-6 pt-4 border-t border-slate-200 dark:border-slate-700">
      <h3 className="text-xl font-bold text-center text-slate-900 dark:text-slate-100">採点結果</h3>
      
      <div className="flex flex-col md:flex-row items-center justify-center md:space-x-12 space-y-6 md:space-y-0 p-6 bg-slate-50 dark:bg-slate-800 rounded-xl">
        <div>
            <h4 className="text-center font-semibold text-slate-600 dark:text-slate-300 mb-2">総合スコア</h4>
            <ScoreCircle score={result.overallScore} />
        </div>
        <div className="text-center">
            <h4 className="font-semibold text-slate-600 dark:text-slate-300 mb-2">模範解答との類似度</h4>
            <p className="text-4xl font-bold text-indigo-500">{result.similarityScore}%</p>
        </div>
      </div>

      <div className="space-y-4">
        <h4 className="font-semibold text-lg flex items-center"><DocumentTextIcon className="h-5 w-5 mr-2 text-indigo-500"/>ルーブリック評価</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {result.rubricScores.map((item) => (
            <RubricItemDisplay key={item.criterion} item={item} />
          ))}
        </div>
      </div>
      
      <div className="space-y-2">
         <h4 className="font-semibold text-lg flex items-center"><LightBulbIcon className="h-5 w-5 mr-2 text-yellow-500"/>総評</h4>
        <div className="p-4 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg text-sm text-slate-700 dark:text-slate-200 leading-relaxed prose prose-sm dark:prose-invert max-w-none">
            {result.overallFeedback}
        </div>
      </div>
    </div>
  );
};
   