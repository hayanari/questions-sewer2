
import React from 'react';

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-8">
       <div className="w-12 h-12 border-4 border-t-indigo-600 border-r-indigo-600 border-b-indigo-200 border-l-indigo-200 rounded-full animate-spin"></div>
       <p className="text-sm text-slate-500 dark:text-slate-400 animate-pulse">AIが採点中です...</p>
    </div>
  );
};
   