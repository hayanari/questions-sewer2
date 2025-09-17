
import React from 'react';

interface ErrorDisplayProps {
  message: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message }) => {
  return (
    <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg my-4 animate-fade-in dark:bg-red-900/30 dark:border-red-700 dark:text-red-200">
      <p className="font-semibold">エラーが発生しました</p>
      <p className="text-sm">{message}</p>
    </div>
  );
};
   