
import React from 'react';
import { BrainCircuitIcon } from './icons';

export const Header: React.FC = () => {
  return (
    <header className="bg-white dark:bg-slate-800 shadow-md">
      <div className="container mx-auto max-w-4xl p-4 flex items-center justify-center">
        <BrainCircuitIcon className="h-8 w-8 text-indigo-500 mr-3" />
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">
          Exam Prep AI Grader
        </h1>
      </div>
    </header>
  );
};
   