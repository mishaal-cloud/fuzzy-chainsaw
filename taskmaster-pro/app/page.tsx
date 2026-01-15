export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            TaskMaster Pro
          </h1>
          <p className="text-xl text-gray-700 mb-8">
            A comprehensive full-stack SaaS demonstration
          </p>

          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Infrastructure Components
            </h2>

            <div className="grid md:grid-cols-2 gap-4">
              <InfraCard
                title="Frontend"
                items={["Next.js 14 App Router", "TypeScript", "Tailwind CSS"]}
              />
              <InfraCard
                title="Database"
                items={["PostgreSQL (Vercel)", "Prisma ORM", "Type-safe queries"]}
              />
              <InfraCard
                title="Authentication"
                items={["NextAuth.js", "GitHub OAuth", "Session management"]}
              />
              <InfraCard
                title="API Routes"
                items={["RESTful endpoints", "Zod validation", "Error handling"]}
              />
              <InfraCard
                title="External APIs"
                items={["OpenAI integration", "AI task suggestions", "Rate limiting"]}
              />
              <InfraCard
                title="File Storage"
                items={["Vercel Blob", "Upload handling", "Image optimization"]}
              />
              <InfraCard
                title="Background Jobs"
                items={["Vercel Cron", "Scheduled tasks", "Email reminders"]}
              />
              <InfraCard
                title="Email Service"
                items={["Resend API", "Transactional emails", "Templates"]}
              />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Environment Variables Required
            </h2>
            <ul className="space-y-2 text-gray-700">
              <li>✅ <code className="bg-gray-100 px-2 py-1 rounded">DATABASE_URL</code> - PostgreSQL connection</li>
              <li>✅ <code className="bg-gray-100 px-2 py-1 rounded">NEXTAUTH_SECRET</code> - Auth secret</li>
              <li>✅ <code className="bg-gray-100 px-2 py-1 rounded">GITHUB_ID/SECRET</code> - OAuth credentials</li>
              <li>✅ <code className="bg-gray-100 px-2 py-1 rounded">OPENAI_API_KEY</code> - AI features</li>
              <li>✅ <code className="bg-gray-100 px-2 py-1 rounded">BLOB_READ_WRITE_TOKEN</code> - File storage</li>
              <li>✅ <code className="bg-gray-100 px-2 py-1 rounded">RESEND_API_KEY</code> - Email service</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfraCard({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <h3 className="font-semibold text-lg mb-2 text-gray-900">{title}</h3>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-gray-600">• {item}</li>
        ))}
      </ul>
    </div>
  );
}
