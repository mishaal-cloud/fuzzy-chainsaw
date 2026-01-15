// AI Suggestions API - Generate AI-powered task suggestions
import { NextRequest } from "next/server";
import { prisma } from "@/lib/prisma";
import {
  requireAuth,
  errorResponse,
  successResponse,
  handleApiError,
} from "@/lib/api-helpers";
import { generateTaskSuggestion } from "@/lib/openai";

type RouteContext = {
  params: { id: string };
};

// POST /api/tasks/[id]/ai-suggest - Generate AI suggestions for task
export async function POST(
  request: NextRequest,
  { params }: RouteContext
) {
  try {
    const user = await requireAuth();

    // Get task
    const task = await prisma.task.findFirst({
      where: {
        id: params.id,
        userId: user.id,
      },
    });

    if (!task) {
      return errorResponse("Task not found", 404);
    }

    // Generate AI suggestion
    const suggestion = await generateTaskSuggestion(
      task.title,
      task.description || undefined
    );

    // Update task with AI suggestion
    const updatedTask = await prisma.task.update({
      where: { id: params.id },
      data: { aiSuggestion: suggestion },
    });

    return successResponse({
      task: updatedTask,
      suggestion,
    });
  } catch (error) {
    return handleApiError(error);
  }
}
