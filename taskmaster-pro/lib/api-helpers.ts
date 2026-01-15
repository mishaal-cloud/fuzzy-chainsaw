// API helper functions
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "./auth";
import { z } from "zod";

// Get authenticated user
export async function getAuthUser() {
  const session = await getServerSession(authOptions);

  if (!session?.user?.email) {
    return null;
  }

  return session.user;
}

// Require authentication
export async function requireAuth() {
  const user = await getAuthUser();

  if (!user) {
    throw new Error("Unauthorized");
  }

  return user;
}

// API error response
export function errorResponse(message: string, status: number = 400) {
  return NextResponse.json(
    { error: message },
    { status }
  );
}

// API success response
export function successResponse(data: any, status: number = 200) {
  return NextResponse.json(data, { status });
}

// Validate request body with Zod
export async function validateBody<T>(
  request: NextRequest,
  schema: z.ZodSchema<T>
): Promise<T> {
  try {
    const body = await request.json();
    return schema.parse(body);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new Error(
        error.errors.map((e) => `${e.path.join(".")}: ${e.message}`).join(", ")
      );
    }
    throw new Error("Invalid request body");
  }
}

// Handle API errors
export function handleApiError(error: unknown) {
  console.error("API Error:", error);

  if (error instanceof Error) {
    if (error.message === "Unauthorized") {
      return errorResponse("Unauthorized", 401);
    }
    return errorResponse(error.message, 400);
  }

  return errorResponse("Internal server error", 500);
}
