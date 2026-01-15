// Email service using Resend
import { Resend } from "resend";
import { prisma } from "./prisma";

const resend = new Resend(process.env.RESEND_API_KEY);
const fromEmail = process.env.RESEND_FROM_EMAIL || "TaskMaster Pro <onboarding@resend.dev>";

// Send task reminder email
export async function sendTaskReminder(
  to: string,
  taskTitle: string,
  dueDate: Date
) {
  try {
    const { data, error } = await resend.emails.send({
      from: fromEmail,
      to,
      subject: `Reminder: ${taskTitle} is due soon`,
      html: `
        <h2>Task Reminder</h2>
        <p>This is a reminder that your task is due soon:</p>
        <h3>${taskTitle}</h3>
        <p><strong>Due:</strong> ${dueDate.toLocaleDateString()}</p>
        <p>Visit TaskMaster Pro to view and complete your task.</p>
      `,
    });

    if (error) {
      throw error;
    }

    // Log email
    await prisma.emailLog.create({
      data: {
        to,
        subject: `Reminder: ${taskTitle} is due soon`,
        template: "task_reminder",
        status: "sent",
        sentAt: new Date(),
      },
    });

    return data;
  } catch (error) {
    console.error("Failed to send email:", error);

    // Log failed email
    await prisma.emailLog.create({
      data: {
        to,
        subject: `Reminder: ${taskTitle} is due soon`,
        template: "task_reminder",
        status: "failed",
        error: error instanceof Error ? error.message : "Unknown error",
      },
    });

    throw error;
  }
}

// Send welcome email
export async function sendWelcomeEmail(to: string, name: string) {
  try {
    const { data, error } = await resend.emails.send({
      from: fromEmail,
      to,
      subject: "Welcome to TaskMaster Pro!",
      html: `
        <h2>Welcome to TaskMaster Pro, ${name}!</h2>
        <p>We're excited to have you on board.</p>
        <p>TaskMaster Pro helps you manage your tasks with AI-powered suggestions and smart reminders.</p>
        <h3>Get Started:</h3>
        <ul>
          <li>Create your first task</li>
          <li>Try AI-powered suggestions</li>
          <li>Upload attachments</li>
          <li>Set reminders</li>
        </ul>
        <p>Happy task managing!</p>
      `,
    });

    if (error) {
      throw error;
    }

    await prisma.emailLog.create({
      data: {
        to,
        subject: "Welcome to TaskMaster Pro!",
        template: "welcome",
        status: "sent",
        sentAt: new Date(),
      },
    });

    return data;
  } catch (error) {
    console.error("Failed to send welcome email:", error);

    await prisma.emailLog.create({
      data: {
        to,
        subject: "Welcome to TaskMaster Pro!",
        template: "welcome",
        status: "failed",
        error: error instanceof Error ? error.message : "Unknown error",
      },
    });
  }
}
