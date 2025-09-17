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
            description: "各ルーブリック項目ごとのスコアとフィードバックの配列です。",
            items: {
                type: Type.OBJECT,
                properties: {
                    criterion: { type: Type.STRING, description: "評価基準（例：「正確性」「網羅性」「論理構成」）です。"},
                    score: { type: Type.INTEGER, description: "この基準のスコアです。" },
                    maxScore: { type: Type.INTEGER, description: "この基準の最大スコアです。" },
                    feedback: { type: Type.STRING, description: "この基準に関する具体的なフィードバックです。" },
                },
                required: ["criterion", "score", "maxScore", "feedback"]
            }
        },
        similarityScore: {
            type: Type.INTEGER,
            description: "ユーザーの回答と模範解答の意味的な類似度を示す0から100のスコアです。"
        },
        overallScore: {
            type: Type.INTEGER,
            description: "最終的な総合スコアで、パーセンテージ（0-100）で計算されます。"
        },
        overallFeedback: {
            type: Type.STRING,
            description: "ユーザーに対する包括的で、建設的で、励みになるような総合的なフィードバックの要約です。"
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

        const jsonText = response.text.trim();
        const result = JSON.parse(jsonText) as GradingResult;
        
        // Basic validation
        if (!result.rubricScores || !result.overallFeedback) {
            throw new Error("Invalid response structure from Gemini API.");
        }

        return result;
    } catch (error) {
        console.error("Error calling Gemini API:", error);
        if (error instanceof Error && error.message.includes('429')) {
             throw new Error("現在サーバーが混み合っています。しばらくしてから再度お試しください。");
        }
        throw new Error("AIからの応答取得に失敗しました。モデルが過負荷になっているか、不正な応答を返した可能性があります。");
    }
};