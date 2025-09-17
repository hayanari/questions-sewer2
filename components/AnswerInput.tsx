
import React from 'react';
import { PaperAirplaneIcon } from './icons';

interface AnswerInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
  isLoading: boolean;
  isGraded: boolean;
}

export const AnswerInput: React.FC<AnswerInputProps> = ({ value, onChange, onSubmit, isLoading, isGraded }) => {
  const charLimit = 100;
  const isOverLimit = value.length > charLimit;
  const isSubmitDisabled = isLoading || isGraded || isOverLimit || !value.trim();

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        if (!isSubmitDisabled) {
            onSubmit();
        }
    }
  };
  
  const textareaClassName = [
    'w-full', 'h-40', 'p-4', 'pr-12', 'border-2', 'rounded-lg',
    'focus:ring-2', 'dark:bg-slate-700', 'dark:border-slate-600',
    'dark:placeholder-slate-400', 'dark:text-white',
    'transition-colors', 'duration-200',
    isOverLimit 
      ? 'border-red-500 focus:ring-red-500 focus:border-red-500 dark:border-red-500'
      : 'border-slate-300 focus:ring-indigo-500 focus:border-indigo-500'
  ].join(' ');

  return (
    <div>
      <div className="relative">
        <textarea
          value={value}
          onChange={onChange}
          onKeyDown={handleKeyDown}
          placeholder="ここに回答を入力してください... (Cmd/Ctrl + Enterで送信)"
          className={textareaClassName}
          disabled={isLoading || isGraded}
          aria-invalid={isOverLimit}
          aria-describedby="char-count"
        />
        <button
          onClick={onSubmit}
          disabled={isSubmitDisabled}
          className={`absolute bottom-3 right-3 p-2 rounded-full transition-all duration-300 ease-in-out ${
            isSubmitDisabled
              ? 'bg-slate-400 dark:bg-slate-600 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white transform hover:scale-110 focus:outline-none focus:ring-4 focus:ring-indigo-300 dark:focus:ring-indigo-800'
          }`}
          aria-label="Submit Answer"
        >
          <PaperAirplaneIcon className="h-5 w-5" />
        </button>
      </div>
       <p 
        id="char-count" 
        className={`text-sm text-right mt-1 pr-1 ${isOverLimit ? 'text-red-600 dark:text-red-400 font-medium' : 'text-slate-500 dark:text-slate-400'}`}
        aria-live="polite"
      >
        {value.length} / {charLimit}
      </p>
    </div>
  );
};
