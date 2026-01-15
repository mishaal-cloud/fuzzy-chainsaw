// Tasks API - GET, PATCH, DELETE for individual task
import { NextRequest } from "next/server";
import { prisma } from "@/lib/prisma";
import {
  requireAuth,
  errorResponse,
  successResponse,
  validateBody,
  handleApiError,
} from "@/lib/api-helpers";
import { updateTaskSchema } from "@/lib/validations";

type RouteContext = {
  params: { id: string };
};

// GET /api/tasks/[id] - Get single task
export async function GET(
  request: NextRequest,
  { params }: RouteContext
) {
  try {
    const user = await requireAuth();

    const task = await prisma.task.findFirst({
      where: {
        id: params.id,
        userId: user.id,
      },
      include: {
        tags: true,
        comments: {
          include: {
            user: {
              select: { name: true, image: true },
            },
          },
          orderBy: { createdAt: "desc" },
        },
      },
    });

    if (!task) {
      return errorResponse("Task not found", 404);
    }

    return successResponse({ task });
  } catch (error) {
    return handleApiError(error);
  }
}

// PATCH /api/tasks/[id] - Update task
export async function PATCH(
  request: NextRequest,
  { params }: RouteContext
) {
  try {
    const user = await requireAuth();
    const data = await validateBody(request, updateTaskSchema);

    // Verify ownership
    const existing = await prisma.task.findFirst({
      where: { id: params.id, userId: user.id },
    });

    if (!existing) {
      return errorResponse("Task not found", 404);
    }

    const task = await prisma.task.update({
      where: { id: params.id },
      data: {
        ...data,
        dueDate: data.dueDate ? new Date(data.dueDate) : undefined,
        completedAt: data.status === "DONE" ? new Date() : undefined,
      },
      include: {
        tags: true,
      },
    });

    return successResponse({ task });
  } catch (error) {
    return handleApiError(error);
  }
}

// DELETE /api/tasks/[id] - Delete task
export async function DELETE(
  request: NextRequest,
  { params }: RouteContext
) {
  try {
    const user = await requireAuth();

    // Verify ownership
    const existing = await prisma.task.findFirst({
      where: { id: params.id, userId: user.id },
    });

    if (!existing) {
      return errorResponse("Task not found", 404);
    }

    await prisma.task.delete({
      where: { id: params.id },
    });

    return successResponse({ message: "Task deleted" });
  } catch (error) {
    return handleApiError(error);
  }
}
