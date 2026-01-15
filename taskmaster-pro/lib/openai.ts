// OpenAI API integration
import OpenAI from "openai";

if (!process.env.OPENAI_API_KEY) {
  throw new Error("OPENAI_API_KEY is not set");
}

export const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Generate AI-powered task suggestions
export async function generateTaskSuggestion(
  taskTitle: string,
  taskDescription?: string
): Promise<string> {
  try {
    const prompt = `As a productivity assistant, provide helpful suggestions for completing this task:

Task: ${taskTitle}
${taskDescription ? `Description: ${taskDescription}` : ""}

Provide 3-5 actionable suggestions to help complete this task effectively. Be specific and practical.`;

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "You are a helpful productivity assistant. Provide clear, actionable suggestions.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
      max_tokens: 300,
      temperature: 0.7,
    });

    return completion.choices[0]?.message?.content || "No suggestions available";
  } catch (error) {
    console.error("OpenAI API error:", error);
    throw new Error("Failed to generate AI suggestions");
  }
}

// Generate task breakdown
export async function generateTaskBreakdown(taskTitle: string): Promise<string[]> {
  try {
    const prompt = `Break down this task into smaller, actionable subtasks:

Task: ${taskTitle}

Provide 3-5 subtasks as a numbered list. Each subtask should be specific and achievable.`;

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: "You are a task planning assistant. Break down tasks into clear subtasks.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
      max_tokens: 200,
      temperature: 0.7,
    });

    const content = completion.choices[0]?.message?.content || "";

    // Parse numbered list
    const subtasks = content
      .split("\n")
      .filter((line) => line.trim().match(/^\d+\./))
      .map((line) => line.replace(/^\d+\.\s*/, "").trim());

    return subtasks;
  } catch (error) {
    console.error("OpenAI API error:", error);
    throw new Error("Failed to generate task breakdown");
  }
}
