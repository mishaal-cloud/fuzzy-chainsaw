// Zod validation schemas for API requests
import { z } from "zod";

// Task validation
export const createTaskSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title too long"),
  description: z.string().max(2000, "Description too long").optional(),
  status: z.enum(["TODO", "IN_PROGRESS", "DONE", "ARCHIVED"]).default("TODO"),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "URGENT"]).default("MEDIUM"),
  dueDate: z.string().datetime().optional(),
  tags: z.array(z.string()).optional(),
});

export const updateTaskSchema = createTaskSchema.partial();

export const taskIdSchema = z.object({
  id: z.string().cuid("Invalid task ID"),
});

// Comment validation
export const createCommentSchema = z.object({
  content: z.string().min(1, "Comment cannot be empty").max(1000, "Comment too long"),
  taskId: z.string().cuid("Invalid task ID"),
});

// AI suggestion validation
export const aiSuggestionSchema = z.object({
  taskId: z.string().cuid("Invalid task ID"),
});

// File upload validation
export const fileUploadSchema = z.object({
  filename: z.string(),
  contentType: z.string(),
  size: z.number().max(10 * 1024 * 1024, "File too large (max 10MB)"),
});

export type CreateTaskInput = z.infer<typeof createTaskSchema>;
export type UpdateTaskInput = z.infer<typeof updateTaskSchema>;
export type CreateCommentInput = z.infer<typeof createCommentSchema>;
export type AISuggestionInput = z.infer<typeof aiSuggestionSchema>;
export type FileUploadInput = z.infer<typeof fileUploadSchema>;
