# Claude Code Reference Card

Copy and paste this into your Claude Code session when working on this project.

## Project Context

```
This is TaskMaster Pro, a Next.js 14 full-stack SaaS application.

DEPLOYMENT:
- Platform: Vercel
- Deploy command: vercel --prod
- Dev command: npm run dev (runs on http://localhost:3000)
- Build command: npm run build

STACK:
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS
- Database: PostgreSQL via Vercel Postgres
- ORM: Prisma (schema in prisma/schema.prisma)
- Authentication: NextAuth.js with GitHub OAuth
- AI: OpenAI API (gpt-4o-mini model)
- File Storage: Vercel Blob
- Email: Resend
- Background Jobs: Vercel Cron (configured in vercel.json)

EXTERNAL SERVICES:
1. Vercel Postgres - Database (auto-connected)
2. GitHub OAuth - User authentication
3. OpenAI API - AI-powered task suggestions
4. Vercel Blob - File uploads and storage
5. Resend - Transactional emails
6. Vercel Cron - Scheduled background jobs

ENVIRONMENT VARIABLES:
All secrets are stored in Vercel environment variables:
- DATABASE_URL (auto-set by Vercel Postgres)
- NEXTAUTH_URL, NEXTAUTH_SECRET
- GITHUB_ID, GITHUB_SECRET
- OPENAI_API_KEY
- BLOB_READ_WRITE_TOKEN (auto-set by Vercel Blob)
- RESEND_API_KEY, RESEND_FROM_EMAIL
- CRON_SECRET

PROJECT STRUCTURE:
- app/ - Next.js app directory (pages and API routes)
- lib/ - Shared utilities (prisma, auth, openai, email)
- prisma/ - Database schema and migrations
- components/ - React components (empty, ready for UI)

DATABASE:
- Run migrations: npx prisma db push
- Generate Prisma client: npx prisma generate
- Open Prisma Studio: npx prisma studio

API ROUTES:
- POST /api/auth/[...nextauth] - Authentication
- GET/POST /api/tasks - List/create tasks
- GET/PATCH/DELETE /api/tasks/[id] - Task operations
- POST /api/tasks/[id]/ai-suggest - Get AI suggestions
- POST /api/upload - Upload file
- GET /api/cron/task-reminders - Daily reminder job

IMPORTANT NOTES:
- All API routes require authentication (except auth endpoints)
- Use Zod for request validation (schemas in lib/validations.ts)
- Prisma client is imported from lib/prisma.ts
- Auth config is in lib/auth.ts
- OpenAI integration is in lib/openai.ts
- Email service is in lib/email.ts

WHEN MAKING CHANGES:
1. Test locally with npm run dev
2. Check types with npm run build
3. Test database changes with npx prisma db push
4. Deploy with vercel --prod

DEPLOYMENT CHECKLIST:
- Ensure all environment variables are set in Vercel
- Run database migrations
- Update GitHub OAuth callback URL for production
- Test all integrations after deployment
```

## Common Commands

```bash
# Development
npm install              # Install dependencies
npm run dev              # Start dev server (localhost:3000)
npm run build            # Build for production
npm run start            # Run production build

# Database
npx prisma db push       # Push schema to database
npx prisma generate      # Generate Prisma Client
npx prisma studio        # Open database GUI

# Deployment
vercel                   # Deploy to preview
vercel --prod            # Deploy to production
vercel logs              # View deployment logs
vercel env ls            # List environment variables
```

## Quick Fixes

### Database Connection Failed
```bash
npx prisma db push
npx prisma generate
```

### Authentication Not Working
Check:
- NEXTAUTH_URL matches your domain
- NEXTAUTH_SECRET is set
- GITHUB_ID and GITHUB_SECRET are correct
- GitHub OAuth callback URL is correct

### OpenAI Errors
- Verify OPENAI_API_KEY is set and valid
- Check OpenAI dashboard for usage/limits
- Ensure API key has sufficient credits

### File Upload Errors
- Verify Vercel Blob is created in dashboard
- Check BLOB_READ_WRITE_TOKEN is set
- File size limit: 10MB
- Allowed types: images, PDFs, text files

### Email Not Sending
- Verify RESEND_API_KEY is correct
- Use onboarding@resend.dev for testing
- Check Resend dashboard for delivery logs

## When to Use What

**For Claude Code to know when to use each service:**

- **Database (Prisma)**: Saving/retrieving data (tasks, users, comments)
- **GitHub OAuth**: User login, getting user info
- **OpenAI**: AI suggestions, smart features
- **Vercel Blob**: File uploads, storing attachments
- **Resend**: Sending emails (reminders, notifications)
- **Cron**: Scheduled tasks (daily reminders, cleanup)

## File Locations

```
Important files:
- prisma/schema.prisma - Database schema
- lib/auth.ts - NextAuth configuration
- lib/prisma.ts - Database client
- lib/openai.ts - OpenAI integration
- lib/email.ts - Email service
- lib/validations.ts - Zod schemas
- lib/api-helpers.ts - API utilities
- app/api/ - All API endpoints
- vercel.json - Cron job configuration
```

## For Claude Code AI

When you see this project:
1. It's a Next.js app that deploys to Vercel
2. All external services are already configured
3. Environment variables are set in Vercel
4. Use `npm run dev` for local testing
5. Use `vercel --prod` to deploy
6. Database schema is in prisma/schema.prisma
7. API routes are in app/api/
8. Authentication is handled by NextAuth.js
9. All secrets are in environment variables (never hardcode)
10. Test locally before deploying

This reference card should give you complete context about the project's infrastructure and how everything connects.
