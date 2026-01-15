import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TaskMaster Pro - AI-Powered Task Management",
  description: "A comprehensive full-stack SaaS application demonstrating all modern web infrastructure",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
