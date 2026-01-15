# TaskMaster Pro - Full-Stack SaaS Demo

A comprehensive full-stack application demonstrating **every major infrastructure component** you need to build modern web applications with Claude Code.

## What This Demonstrates

This is a complete, production-ready SaaS application showing:

1. **Frontend**: Next.js 14, TypeScript, Tailwind CSS
2. **Database**: PostgreSQL with Prisma ORM
3. **Authentication**: NextAuth.js with GitHub OAuth
4. **API Routes**: RESTful CRUD with validation
5. **External APIs**: OpenAI integration
6. **File Storage**: Vercel Blob
7. **Background Jobs**: Vercel Cron
8. **Email**: Resend for transactional emails

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  - App Router with Server Components                    │
│  - TypeScript + Tailwind CSS                            │
│  - Client & Server-side rendering                       │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              API Routes (Next.js API)                    │
│  - RESTful endpoints with Zod validation               │
│  - Authentication middleware                            │
│  - Error handling                                       │
└─┬──────┬──────┬──────┬──────┬──────────────────────────┘
  │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼
┌─────┐ ┌────┐ ┌────┐ ┌────┐ ┌──────┐
│ DB  │ │Auth│ │ AI │ │File│ │Email │
│Psql │ │Next│ │GPT │ │Blob│ │Resnd │
└─────┘ └────┘ └────┘ └────┘ └──────┘
```

## Infrastructure Requirements

### Required Services

| Service | Purpose | How to Get |
|---------|---------|------------|
| **Vercel** | Hosting & deployment | [vercel.com](https://vercel.com) |
| **Vercel Postgres** | Database | Enable in Vercel dashboard |
| **GitHub OAuth** | Authentication | [GitHub Developer Settings](https://github.com/settings/developers) |
| **OpenAI API** | AI features | [platform.openai.com](https://platform.openai.com) |
| **Vercel Blob** | File storage | Enable in Vercel dashboard |
| **Resend** | Email service | [resend.com](https://resend.com) |

### Cost Estimate

- **Free Tier**: $0/month (hobby projects)
- **Minimal Usage**: ~$10-20/month
  - Vercel Pro: $20/month (optional)
  - OpenAI: ~$5/month for light usage
  - Everything else: Free tier

## Setup Instructions

### 1. Clone and Install

```bash
cd taskmaster-pro
npm install
```

### 2. Set Up Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Link project
vercel link
```

### 3. Set Up Database (Vercel Postgres)

```bash
# In Vercel dashboard:
# 1. Go to Storage tab
# 2. Create Vercel Postgres database
# 3. Copy DATABASE_URL

# Then run migrations
npx prisma db push
npx prisma generate
```

### 4. Set Up GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create New OAuth App
3. **Homepage URL**: `http://localhost:3000`
4. **Callback URL**: `http://localhost:3000/api/auth/callback/github`
5. Copy Client ID and Client Secret

### 5. Set Up OpenAI API

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new API key
3. Copy the key (starts with `sk-`)

### 6. Set Up Resend

1. Go to [Resend](https://resend.com)
2. Create account and verify domain (or use test domain)
3. Create API key
4. Copy the key

### 7. Set Up Vercel Blob

```bash
# In Vercel dashboard:
# 1. Go to Storage tab
# 2. Create Vercel Blob storage
# 3. Token is automatically set in environment variables
```

### 8. Configure Environment Variables

Create `.env.local`:

```bash
# Copy example
cp .env.example .env.local

# Edit with your values
nano .env.local
```

Required variables:
```bash
DATABASE_URL="postgresql://..."
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="generate-with: openssl rand -base64 32"
GITHUB_ID="your-github-client-id"
GITHUB_SECRET="your-github-client-secret"
OPENAI_API_KEY="sk-your-openai-api-key"
BLOB_READ_WRITE_TOKEN="auto-set-by-vercel"
RESEND_API_KEY="re_your-resend-api-key"
RESEND_FROM_EMAIL="TaskMaster Pro <onboarding@resend.dev>"
CRON_SECRET="generate-with: openssl rand -base64 32"
```

### 9. Set Environment Variables in Vercel

```bash
# Set each variable
vercel env add DATABASE_URL
vercel env add NEXTAUTH_SECRET
vercel env add GITHUB_ID
vercel env add GITHUB_SECRET
vercel env add OPENAI_API_KEY
vercel env add RESEND_API_KEY
vercel env add RESEND_FROM_EMAIL
vercel env add CRON_SECRET

# Pull environment variables locally
vercel env pull .env.local
```

### 10. Run Development Server

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

### 11. Deploy to Production

```bash
# Deploy
vercel --prod

# Update GitHub OAuth callback URL to production URL
# https://your-domain.vercel.app/api/auth/callback/github
```

## Project Structure

```
taskmaster-pro/
├── app/
│   ├── api/
│   │   ├── auth/[...nextauth]/      # Authentication
│   │   ├── tasks/                   # Task CRUD
│   │   │   └── [id]/
│   │   │       └── ai-suggest/      # AI suggestions
│   │   ├── upload/                  # File uploads
│   │   └── cron/
│   │       └── task-reminders/      # Scheduled jobs
│   ├── globals.css                  # Styles
│   ├── layout.tsx                   # Root layout
│   └── page.tsx                     # Homepage
├── lib/
│   ├── prisma.ts                    # Prisma client
│   ├── auth.ts                      # NextAuth config
│   ├── openai.ts                    # OpenAI integration
│   ├── email.ts                     # Resend email
│   ├── validations.ts               # Zod schemas
│   └── api-helpers.ts               # API utilities
├── prisma/
│   └── schema.prisma                # Database schema
├── .env.example                     # Environment template
├── .env.local                       # Local secrets (git-ignored)
├── vercel.json                      # Vercel config (cron jobs)
├── package.json                     # Dependencies
└── README.md                        # This file
```

## API Endpoints

### Authentication
- `GET/POST /api/auth/*` - NextAuth.js endpoints

### Tasks
- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create task
- `GET /api/tasks/[id]` - Get task
- `PATCH /api/tasks/[id]` - Update task
- `DELETE /api/tasks/[id]` - Delete task
- `POST /api/tasks/[id]/ai-suggest` - Get AI suggestions

### File Upload
- `POST /api/upload` - Upload file to Blob storage
- `DELETE /api/upload?url=[url]` - Delete file

### Cron Jobs
- `GET /api/cron/task-reminders` - Send task reminders (runs daily at 9 AM)

## Database Schema

### Core Models
- **User** - User accounts (NextAuth)
- **Account** - OAuth accounts (NextAuth)
- **Session** - User sessions (NextAuth)
- **Task** - User tasks with AI suggestions
- **Comment** - Task comments
- **Tag** - Task tags
- **CronJob** - Background job tracking
- **EmailLog** - Email tracking

See `prisma/schema.prisma` for full schema.

## Deployment Checklist

- [ ] Vercel account created
- [ ] GitHub OAuth app created
- [ ] OpenAI API key obtained
- [ ] Resend account created
- [ ] Vercel Postgres database created
- [ ] Vercel Blob storage created
- [ ] All environment variables set in Vercel
- [ ] Database migrations run (`npx prisma db push`)
- [ ] GitHub OAuth callback updated to production URL
- [ ] Test all integrations work

## Common Issues

### Database Connection Error
```bash
# Ensure DATABASE_URL is set correctly
npx prisma db push
```

### NextAuth Error
```bash
# Generate new secret
openssl rand -base64 32

# Set NEXTAUTH_URL to your domain
NEXTAUTH_URL=https://your-domain.vercel.app
```

### OpenAI Rate Limit
```bash
# Add usage limits in OpenAI dashboard
# Use gpt-4o-mini for lower costs
```

### Blob Upload Fails
```bash
# Ensure Vercel Blob is created in dashboard
# Check BLOB_READ_WRITE_TOKEN is set
```

## For Claude Code

When asking Claude Code to work on this project, tell it:

> "This is a Next.js full-stack app that deploys to Vercel using `vercel --prod`.
> It uses PostgreSQL (Vercel Postgres), NextAuth.js for auth, OpenAI for AI features,
> Vercel Blob for file storage, and Resend for emails. Run `npm run dev` for development."

Claude Code will then know:
- Where to deploy (Vercel)
- How to run locally (`npm run dev`)
- What external services are used
- How to build (`npm run build`)

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [NextAuth.js Documentation](https://next-auth.js.org)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Resend Documentation](https://resend.com/docs)

## License

MIT
