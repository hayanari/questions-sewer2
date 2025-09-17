
import { GoogleGenAI, Type } from "@google/genai";
import { type Question, type GradingResult } from '../types';

if (!process.env.API_KEY) {
    throw new Error("API_KEY environment variable is not set.");
}

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const gradingSchema = {
    type: Type.OBJECT,
    properties: {
        rubricScores: {
            type: Type.ARRAY,
            description: "An array of rubric items with scores and feedback.",
            items: {
                type: Type.OBJECT,
                properties: {
                    criterion: { type: Type.STRING, description: "The evaluation criterion (e.g., '正確性', '網羅性', '論理構成')."},
                    score: { type: Type.INTEGER, description: "Score for this criterion." },
                    maxScore: { type: Type.INTEGER, description: "Maximum possible score for this criterion." },
                    feedback: { type: Type.STRING, description: "Specific feedback for this criterion." },
                },
                required: ["criterion", "score", "maxScore", "feedback"]
            }
        },
        similarityScore: {
            type: Type.INTEGER,
            description: "A score from 0 to 100 indicating the semantic similarity between the user's answer and the model answer."
        },
        overallScore: {
            type: Type.INTEGER,
            description: "The final overall score, calculated as a percentage (0-100)."
        },
        overallFeedback: {
            type: Type.STRING,
            description: "A comprehensive, constructive, and encouraging overall feedback summary for the user."
        }
    },
    required: ["rubricScores", "similarityScore", "overallScore", "overallFeedback"]
};

export const gradeAnswer = async (question: Question, userAnswer: string): Promise<GradingResult> => {
    const prompt = `
あなたは経験豊富な教育者であり、試験の採点者です。以下の情報に基づいて、受験者の回答を厳格かつ公正に採点してください。

# 指示
1.  **ルーブリック評価**: 以下の3つの評価基準に基づいて、それぞれ10点満点で採点し、具体的なフィードバックを記述してください。
    *   **正確性**: 回答に含まれる情報が事実として正しいか。
    *   **網羅性**: 問題の要求に対して、必要な要素が網羅されているか。
    *   **論理構成**: 回答の構造が論理的で分かりやすいか。
2.  **意味的類似度**: 模範解答と受験者の回答の意味的な類似度を0から100のスコアで評価してください。
3.  **総合評価**: ルーブリック評価と類似度を考慮して、総合スコアを100点満点で算出してください。
4.  **総評**: 受験者に対する励ましを含む、建設的で総合的なフィードバックを生成してください。良かった点と改善点を具体的に指摘してください。
5.  **出力形式**: 結果は必ず指定されたJSON形式で出力してください。

# 問題
## 科目
${question.subject}

## 問題文
${question.text}

# 模範解答
${question.modelAnswer}

# 受験者の回答
${userAnswer}

# 採点結果 (JSON形式で出力)
`;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: gradingSchema,
                temperature: 0.3,
            },
        });

        const jsonText = response.text;
        const result = JSON.parse(jsonText) as GradingResult;
        
        // Basic validation
        if (!result.rubricScores || !result.overallFeedback) {
            throw new Error("Invalid response structure from Gemini API.");
        }

        return result;
    } catch (error) {
        console.error("Error calling Gemini API:", error);
        throw new Error("Failed to get a valid response from the AI. The model may be overloaded. Please try again.");
    }
};
   