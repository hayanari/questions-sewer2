import React from 'react';
import { BookOpenIcon } from './icons';

interface ModelAnswerDisplayProps {
    answer: string;
}

export const ModelAnswerDisplay: React.FC<ModelAnswerDisplayProps> = ({ answer }) => {
    return (
        <div className="mt-6 animate-fade-in">
             <div className="space-y-2">
                 <h4 className="font-semibold text-lg flex items-center"><BookOpenIcon className="h-5 w-5 mr-2 text-green-500"/>模範解答</h4>
                <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg text-sm text-slate-700 dark:text-slate-200 leading-relaxed prose prose-sm dark:prose-invert max-w-none">
                    {answer}
                </div>
            </div>
        </div>
    );
};
