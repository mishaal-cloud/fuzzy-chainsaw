// Tasks API - GET (list) and POST (create)
import { NextRequest } from "next/server";
import { prisma } from "@/lib/prisma";
import {
  requireAuth,
  errorResponse,
  successResponse,
  validateBody,
  handleApiError,
} from "@/lib/api-helpers";
import { createTaskSchema } from "@/lib/validations";

// GET /api/tasks - List all tasks for authenticated user
export async function GET(request: NextRequest) {
  try {
    const user = await requireAuth();

    // Get query parameters
    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status");
    const priority = searchParams.get("priority");

    // Build filter
    const where: any = { userId: user.id };
    if (status) where.status = status;
    if (priority) where.priority = priority;

    const tasks = await prisma.task.findMany({
      where,
      include: {
        tags: true,
        comments: {
          include: {
            user: {
              select: { name: true, image: true },
            },
          },
        },
        _count: {
          select: { comments: true },
        },
      },
      orderBy: { createdAt: "desc" },
    });

    return successResponse({ tasks });
  } catch (error) {
    return handleApiError(error);
  }
}

// POST /api/tasks - Create a new task
export async function POST(request: NextRequest) {
  try {
    const user = await requireAuth();
    const data = await validateBody(request, createTaskSchema);

    const task = await prisma.task.create({
      data: {
        ...data,
        userId: user.id,
        dueDate: data.dueDate ? new Date(data.dueDate) : null,
      },
      include: {
        tags: true,
      },
    });

    return successResponse({ task }, 201);
  } catch (error) {
    return handleApiError(error);
  }
}
