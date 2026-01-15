// Cron job - Send task reminders
// This runs on a schedule configured in vercel.json
import { NextRequest } from "next/server";
import { prisma } from "@/lib/prisma";
import { sendTaskReminder } from "@/lib/email";
import { successResponse, errorResponse } from "@/lib/api-helpers";

export async function GET(request: NextRequest) {
  try {
    // Verify cron secret (Vercel automatically adds this header)
    const authHeader = request.headers.get("authorization");
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return errorResponse("Unauthorized", 401);
    }

    // Find tasks due in the next 24 hours that haven't been completed
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    const tasks = await prisma.task.findMany({
      where: {
        status: {
          in: ["TODO", "IN_PROGRESS"],
        },
        dueDate: {
          gte: new Date(),
          lte: tomorrow,
        },
      },
      include: {
        user: {
          select: {
            email: true,
            name: true,
          },
        },
      },
    });

    // Send reminders
    const results = await Promise.allSettled(
      tasks.map(async (task) => {
        if (task.user.email) {
          await sendTaskReminder(
            task.user.email,
            task.title,
            task.dueDate!
          );
        }
      })
    );

    const successful = results.filter((r) => r.status === "fulfilled").length;
    const failed = results.filter((r) => r.status === "rejected").length;

    // Log cron job
    await prisma.cronJob.create({
      data: {
        name: "task_reminders",
        lastRun: new Date(),
        nextRun: new Date(Date.now() + 24 * 60 * 60 * 1000), // Next day
        status: "completed",
      },
    });

    return successResponse({
      message: "Task reminders sent",
      tasksFound: tasks.length,
      successful,
      failed,
    });
  } catch (error) {
    console.error("Cron job error:", error);

    // Log failed cron job
    await prisma.cronJob.create({
      data: {
        name: "task_reminders",
        lastRun: new Date(),
        status: "failed",
        error: error instanceof Error ? error.message : "Unknown error",
      },
    });

    return errorResponse("Cron job failed", 500);
  }
}
