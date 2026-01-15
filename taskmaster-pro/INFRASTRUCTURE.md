# Infrastructure Map - Complete Connection Guide

This document is your **infrastructure blueprint**. It shows exactly what you need to connect and how everything works together.

## The Complete Picture

```
┌─────────────────────────────────────────────────────────────┐
│                       YOUR APPLICATION                       │
│                     (Next.js on Vercel)                      │
└───────┬──────────┬──────────┬──────────┬──────────┬─────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
    ┌───────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │Database│ │  Auth  │ │   AI   │ │ Files  │ │ Email  │
    │Postgres│ │ GitHub │ │ OpenAI │ │  Blob  │ │ Resend │
    └───────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

## Why You Need Each Connection

### 1. Vercel (Hosting Platform)
**Purpose**: Runs your application
**Alternative**: Railway, Fly.io, AWS
**Why Vercel**:
- Zero-config Next.js deployment
- Built-in CI/CD from Git
- Global edge network
- Integrated database and storage

**What it provides**:
- Web hosting
- Automatic HTTPS
- Automatic deployments from Git
- Environment variable management
- Serverless functions
- Edge network (CDN)

### 2. Database (Vercel Postgres)
**Purpose**: Stores all your data
**Alternative**: Railway Postgres, Supabase, PlanetScale
**Why you need it**: Every app needs to save data

**What it stores**:
- User accounts and profiles
- Tasks and their details
- Comments
- Tags
- Email logs
- Cron job history

**Connection flow**:
```
Next.js API Route → Prisma ORM → PostgreSQL → Data
```

### 3. Authentication (GitHub OAuth)
**Purpose**: User login and identity
**Alternative**: Google OAuth, Auth0, Clerk
**Why you need it**: Users need accounts

**What it provides**:
- User sign-in/sign-up
- Profile information (name, email, avatar)
- Session management
- No password storage needed

**Connection flow**:
```
User clicks "Sign in"
  → Redirects to GitHub
  → User authorizes
  → GitHub sends user data
  → NextAuth creates session
  → User is logged in
```

### 4. AI Features (OpenAI)
**Purpose**: AI-powered capabilities
**Alternative**: Anthropic Claude, Google Gemini
**Why you need it**: Modern apps need AI features

**What it provides**:
- Task suggestions
- Smart recommendations
- Content generation
- Natural language processing

**Connection flow**:
```
User requests AI suggestion
  → API route calls OpenAI
  → OpenAI returns completion
  → Stored in database
  → Displayed to user
```

### 5. File Storage (Vercel Blob)
**Purpose**: Store uploaded files
**Alternative**: AWS S3, Cloudinary, Uploadcare
**Why you need it**: Users need to upload files

**What it provides**:
- Image uploads
- PDF uploads
- Document storage
- Public URLs for files
- Automatic CDN delivery

**Connection flow**:
```
User uploads file
  → API route receives file
  → Uploads to Vercel Blob
  → Returns public URL
  → URL stored in database
```

### 6. Email Service (Resend)
**Purpose**: Send transactional emails
**Alternative**: SendGrid, AWS SES, Postmark
**Why you need it**: Notify users about important events

**What it provides**:
- Task reminder emails
- Welcome emails
- Notification emails
- Email templates
- Delivery tracking

**Connection flow**:
```
Cron job runs daily
  → Finds tasks due soon
  → Calls Resend API
  → Sends reminder emails
  → Logs delivery status
```

### 7. Background Jobs (Vercel Cron)
**Purpose**: Scheduled tasks that run automatically
**Alternative**: Inngest, Quirrel, BullMQ
**Why you need it**: Some tasks need to run on schedule

**What it provides**:
- Daily reminder emails
- Data cleanup
- Report generation
- Automated maintenance

**Connection flow**:
```
Vercel triggers cron job (9 AM daily)
  → Hits /api/cron/task-reminders
  → Verifies CRON_SECRET
  → Processes tasks
  → Sends emails
  → Logs results
```

## How Connections Are Authenticated

### Database Connection
```bash
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```
- Vercel sets this automatically when you create Postgres
- Includes username, password, host, port, database name
- Uses SSL for security

### GitHub OAuth
```bash
GITHUB_ID="abc123..."        # Public identifier
GITHUB_SECRET="secret456..."  # Private key
```
- You create this in GitHub developer settings
- ID is public, Secret is private
- App requests access, GitHub verifies via these credentials

### OpenAI API
```bash
OPENAI_API_KEY="sk-proj-xyz..."
```
- Bearer token authentication
- Sent in HTTP headers
- Each request charges your account

### Vercel Blob
```bash
BLOB_READ_WRITE_TOKEN="vercel_blob_rw_abc123..."
```
- Vercel sets this automatically
- Allows read and write access
- Scoped to your project

### Resend API
```bash
RESEND_API_KEY="re_abc123..."
```
- API key authentication
- Sent in HTTP headers
- Rate limited based on plan

### NextAuth
```bash
NEXTAUTH_SECRET="random-secret-string"
NEXTAUTH_URL="https://your-app.vercel.app"
```
- Secret encrypts session tokens
- URL tells NextAuth where it's running
- Both required for authentication to work

### Cron Jobs
```bash
CRON_SECRET="random-secret-string"
```
- Vercel sends this in Authorization header
- Your API verifies it matches
- Prevents unauthorized execution

## Data Flow Examples

### Example 1: User Creates a Task

```
1. User fills out form in browser
2. Form submits to POST /api/tasks
3. API route validates request with Zod
4. API route checks user is authenticated (NextAuth)
5. API route saves task to database (Prisma → Postgres)
6. Database returns created task
7. API route returns task to client
8. UI updates to show new task
```

### Example 2: User Gets AI Suggestions

```
1. User clicks "Get AI Suggestions" button
2. Request sent to POST /api/tasks/[id]/ai-suggest
3. API route fetches task from database
4. API route calls OpenAI API with task details
5. OpenAI returns AI-generated suggestions
6. API route saves suggestion to database
7. API route returns suggestion to client
8. UI displays suggestion
```

### Example 3: User Uploads File

```
1. User selects file and clicks upload
2. File sent to POST /api/upload (as FormData)
3. API route validates file type and size
4. API route uploads to Vercel Blob
5. Vercel Blob returns public URL
6. API route returns URL to client
7. Client saves URL in task attachment field
8. File is now accessible via URL
```

### Example 4: Daily Reminder Emails

```
1. Vercel triggers cron job at 9 AM
2. GET /api/cron/task-reminders is called
3. API verifies CRON_SECRET
4. API queries database for tasks due today
5. For each task, API calls Resend
6. Resend sends email to user
7. API logs email delivery
8. API returns summary of emails sent
```

## Environment Variables: Complete Reference

| Variable | Source | Purpose | Example |
|----------|--------|---------|---------|
| `DATABASE_URL` | Vercel Postgres | Database connection | `postgresql://...` |
| `NEXTAUTH_URL` | You set | App URL | `https://app.com` |
| `NEXTAUTH_SECRET` | You generate | Session encryption | `abc123...` |
| `GITHUB_ID` | GitHub OAuth | OAuth client ID | `Iv1.abc123...` |
| `GITHUB_SECRET` | GitHub OAuth | OAuth secret | `secret456...` |
| `OPENAI_API_KEY` | OpenAI | API authentication | `sk-proj-xyz...` |
| `BLOB_READ_WRITE_TOKEN` | Vercel Blob | Storage access | `vercel_blob_...` |
| `RESEND_API_KEY` | Resend | Email API access | `re_abc123...` |
| `RESEND_FROM_EMAIL` | You set | Sender email | `app@domain.com` |
| `CRON_SECRET` | You generate | Cron security | `secret789...` |
| `NODE_ENV` | Vercel | Environment | `production` |

## Security Considerations

### What's Public vs Private

**Public** (can be exposed in frontend):
- API endpoints
- Vercel app URL
- Public file URLs from Blob

**Private** (NEVER expose in frontend):
- `DATABASE_URL`
- `GITHUB_SECRET`
- `OPENAI_API_KEY`
- `BLOB_READ_WRITE_TOKEN`
- `RESEND_API_KEY`
- `NEXTAUTH_SECRET`
- `CRON_SECRET`

### How to Keep Secrets Safe

1. **Only use in API routes** (server-side)
2. **Never commit to Git** (use .env.local, add to .gitignore)
3. **Use Vercel's environment variables** (encrypted at rest)
4. **Rotate secrets regularly** (especially if exposed)
5. **Use different secrets for dev/prod**

## Cost Breakdown

### Free Tier Limits

| Service | Free Tier | Overage Cost |
|---------|-----------|--------------|
| Vercel | 100 GB bandwidth | $20/100 GB |
| Postgres | 60 hours compute | $0.0034/hour |
| Blob | 1 GB storage | $0.15/GB |
| OpenAI | None | ~$0.002/request |
| Resend | 100 emails/day | $20/50k emails |

### Realistic Monthly Costs

**Hobby project** (< 1k users):
- Vercel: $0
- Postgres: $0
- Blob: $0
- OpenAI: $5-10
- Resend: $0
- **Total: $5-10/month**

**Small business** (< 10k users):
- Vercel: $20 (Pro plan)
- Postgres: $5-10
- Blob: $0-5
- OpenAI: $20-50
- Resend: $0-20
- **Total: $45-105/month**

## Troubleshooting Connection Issues

### Database won't connect
```bash
# Check variable is set
echo $DATABASE_URL

# Test connection
npx prisma db push

# Common issues:
# - DATABASE_URL not set
# - SSL mode incorrect
# - Database not created in Vercel
```

### GitHub OAuth fails
```bash
# Common issues:
# - Callback URL doesn't match
# - GITHUB_ID or GITHUB_SECRET wrong
# - NEXTAUTH_URL doesn't match actual URL
# - NEXTAUTH_SECRET not set

# Verify:
vercel env ls | grep GITHUB
vercel env ls | grep NEXTAUTH
```

### OpenAI errors
```bash
# Common issues:
# - Invalid API key
# - Rate limit exceeded
# - Insufficient credits

# Test manually:
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

### File uploads fail
```bash
# Common issues:
# - BLOB_READ_WRITE_TOKEN not set
# - Blob storage not created
# - File too large
# - Wrong file type

# Verify:
vercel env ls | grep BLOB
```

### Emails not sending
```bash
# Common issues:
# - RESEND_API_KEY invalid
# - Domain not verified (use onboarding@resend.dev for testing)
# - Rate limit exceeded

# Test:
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from":"onboarding@resend.dev","to":"test@example.com","subject":"Test","html":"Test"}'
```

## Alternatives to This Stack

### If you want cheaper hosting:
- **Railway**: $5/month for everything
- **Fly.io**: Pay for what you use

### If you want simpler database:
- **Supabase**: Built-in auth + database + storage
- **PlanetScale**: Generous free tier

### If you want no-code deployment:
- **Netlify**: Similar to Vercel
- **Cloudflare Pages**: Free, very fast

### If you want self-hosted:
- **Docker + PostgreSQL + Nginx**
- More control, more maintenance

## For Claude Code

Tell Claude Code about your infrastructure:

> "This app has 6 main connections:
> 1. Hosted on Vercel (deploy with `vercel --prod`)
> 2. Database: Vercel Postgres via Prisma
> 3. Auth: GitHub OAuth via NextAuth.js
> 4. AI: OpenAI API for suggestions
> 5. Files: Vercel Blob for uploads
> 6. Email: Resend for notifications
>
> All secrets are in environment variables. Run `npm run dev` locally."

Claude Code will understand:
- Where the app runs
- What services it connects to
- How to deploy it
- What environment variables exist

## Summary

You need **6 accounts**:
1. Vercel (hosting + database + storage)
2. GitHub (OAuth login)
3. OpenAI (AI features)
4. Resend (emails)

You need **11 environment variables**:
1. DATABASE_URL (auto-set)
2. NEXTAUTH_URL
3. NEXTAUTH_SECRET
4. GITHUB_ID
5. GITHUB_SECRET
6. OPENAI_API_KEY
7. BLOB_READ_WRITE_TOKEN (auto-set)
8. RESEND_API_KEY
9. RESEND_FROM_EMAIL
10. CRON_SECRET
11. NODE_ENV

You get a **production-ready** app with:
- User authentication
- Database storage
- AI features
- File uploads
- Email notifications
- Background jobs

This is the **complete infrastructure** you need for modern web applications!
