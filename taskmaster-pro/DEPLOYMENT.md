# Deployment Guide - All Connections You Need

This document explains **every single connection and account** you need to deploy TaskMaster Pro. This is the complete infrastructure map.

## Overview: What You're Connecting

```
Your Computer
     │
     ├─> Vercel (Hosting)
     │    ├─> Vercel Postgres (Database)
     │    └─> Vercel Blob (File Storage)
     │
     ├─> GitHub (OAuth Authentication)
     ├─> OpenAI (AI Features)
     └─> Resend (Email Service)
```

## Complete Setup Walkthrough

### Step 1: Vercel Account & Project

**What**: Hosting platform for Next.js applications
**Cost**: Free for hobby projects
**Why**: Handles deployment, database, file storage

```bash
# 1. Create account at vercel.com
# 2. Install CLI
npm install -g vercel

# 3. Login
vercel login

# 4. Link project
cd taskmaster-pro
vercel link
# Choose: Create new project
# Enter project name: taskmaster-pro
```

**What you get**:
- Deployment URL: `https://taskmaster-pro-xyz.vercel.app`
- Dashboard access: `https://vercel.com/dashboard`

---

### Step 2: Vercel Postgres (Database)

**What**: PostgreSQL database hosted by Vercel
**Cost**: Free tier (60 hours compute/month)
**Why**: Stores all your app data

```bash
# 1. Go to Vercel dashboard
# 2. Select your project
# 3. Go to "Storage" tab
# 4. Click "Create Database"
# 5. Choose "Postgres"
# 6. Name it: taskmaster-pro-db
# 7. Click "Create"
```

**Connection established**:
```
Vercel Project → Vercel Postgres
```

**Environment variable automatically set**:
- `DATABASE_URL` (connection string)
- `POSTGRES_URL`
- `POSTGRES_PRISMA_URL`
- etc.

**Push database schema**:
```bash
# After database is created
npx prisma db push
npx prisma generate
```

---

### Step 3: GitHub OAuth (Authentication)

**What**: Let users sign in with GitHub
**Cost**: Free
**Why**: Handles user authentication

```bash
# 1. Go to: https://github.com/settings/developers
# 2. Click "OAuth Apps"
# 3. Click "New OAuth App"
```

**Fill in**:
- **Application name**: TaskMaster Pro
- **Homepage URL**: `http://localhost:3000` (for development)
- **Authorization callback URL**: `http://localhost:3000/api/auth/callback/github`
- Click "Register application"

**You'll get**:
- Client ID: `abc123...`
- Client Secret: `secret456...` (click "Generate new client secret")

**Add to environment variables**:
```bash
vercel env add GITHUB_ID
# Paste your Client ID

vercel env add GITHUB_SECRET
# Paste your Client Secret
```

**Connection established**:
```
Your App → GitHub OAuth → User Authentication
```

**For production**:
- Add production callback URL in GitHub settings:
- `https://your-domain.vercel.app/api/auth/callback/github`

---

### Step 4: OpenAI API (AI Features)

**What**: AI-powered task suggestions
**Cost**: Pay-as-you-go (starts at ~$0.002 per request)
**Why**: Provides AI features

```bash
# 1. Go to: https://platform.openai.com
# 2. Create account / Sign in
# 3. Go to API Keys: https://platform.openai.com/api-keys
# 4. Click "Create new secret key"
# 5. Name it: "TaskMaster Pro"
# 6. Copy the key (starts with sk-)
```

**Important**: Copy the key immediately - you can't see it again!

**Add to environment variables**:
```bash
vercel env add OPENAI_API_KEY
# Paste your API key
```

**Connection established**:
```
Your App API Routes → OpenAI API → AI Responses
```

**Usage monitoring**:
- Check usage at: https://platform.openai.com/usage
- Set usage limits in dashboard to control costs

---

### Step 5: Vercel Blob (File Storage)

**What**: Object storage for file uploads
**Cost**: Free tier (1 GB storage)
**Why**: Store user-uploaded files

```bash
# 1. Go to Vercel dashboard
# 2. Select your project
# 3. Go to "Storage" tab
# 4. Click "Create Database"
# 5. Choose "Blob"
# 6. Name it: taskmaster-pro-files
# 7. Click "Create"
```

**Connection established**:
```
Vercel Project → Vercel Blob
```

**Environment variable automatically set**:
- `BLOB_READ_WRITE_TOKEN`

**No additional setup needed** - it works automatically!

---

### Step 6: Resend (Email Service)

**What**: Transactional email service
**Cost**: Free tier (100 emails/day)
**Why**: Send task reminders and notifications

```bash
# 1. Go to: https://resend.com
# 2. Create account
# 3. Verify your email
# 4. Go to API Keys: https://resend.com/api-keys
# 5. Click "Create API Key"
# 6. Name it: "TaskMaster Pro"
# 7. Copy the key (starts with re_)
```

**Domain setup (optional but recommended)**:
```bash
# For production emails:
# 1. Go to "Domains" in Resend dashboard
# 2. Add your domain
# 3. Add DNS records to your domain
# 4. Verify domain

# For testing, use:
# onboarding@resend.dev (works without domain verification)
```

**Add to environment variables**:
```bash
vercel env add RESEND_API_KEY
# Paste your API key

vercel env add RESEND_FROM_EMAIL
# Enter: TaskMaster Pro <onboarding@resend.dev>
# Or your verified domain: TaskMaster Pro <noreply@yourdomain.com>
```

**Connection established**:
```
Your App Cron Jobs → Resend API → User Emails
```

---

### Step 7: NextAuth Secret (Security)

**What**: Secret key for session encryption
**Cost**: Free
**Why**: Secure user sessions

```bash
# Generate a secret
openssl rand -base64 32

# Add to Vercel
vercel env add NEXTAUTH_SECRET
# Paste the generated secret
```

---

### Step 8: Cron Secret (Security)

**What**: Secret to protect cron job endpoints
**Cost**: Free
**Why**: Prevent unauthorized cron job execution

```bash
# Generate a secret
openssl rand -base64 32

# Add to Vercel
vercel env add CRON_SECRET
# Paste the generated secret
```

---

### Step 9: NextAuth URL

**What**: Your application URL
**Cost**: Free
**Why**: NextAuth needs to know where it's running

```bash
# Development
vercel env add NEXTAUTH_URL development
# Enter: http://localhost:3000

# Production
vercel env add NEXTAUTH_URL production
# Enter: https://your-domain.vercel.app
```

---

## Summary: All Connections

| Service | What It Does | Account Needed | Cost |
|---------|--------------|----------------|------|
| **Vercel** | Hosting | vercel.com | Free |
| **Vercel Postgres** | Database | (same) | Free tier |
| **Vercel Blob** | File storage | (same) | Free tier |
| **GitHub** | OAuth login | github.com | Free |
| **OpenAI** | AI features | platform.openai.com | Pay-per-use (~$5/mo) |
| **Resend** | Emails | resend.com | Free tier |

## Complete Environment Variables List

```bash
# Database (auto-set by Vercel Postgres)
DATABASE_URL="postgresql://..."

# Authentication
NEXTAUTH_URL="https://your-domain.vercel.app"
NEXTAUTH_SECRET="generated-secret"

# GitHub OAuth (from GitHub developer settings)
GITHUB_ID="your-client-id"
GITHUB_SECRET="your-client-secret"

# OpenAI (from OpenAI platform)
OPENAI_API_KEY="sk-your-key"

# Vercel Blob (auto-set by Vercel Blob)
BLOB_READ_WRITE_TOKEN="auto-generated"

# Resend (from Resend dashboard)
RESEND_API_KEY="re_your-key"
RESEND_FROM_EMAIL="TaskMaster Pro <onboarding@resend.dev>"

# Cron Job Security
CRON_SECRET="generated-secret"

# App Config
NODE_ENV="production"
```

## Setting All Variables at Once

```bash
# Pull .env.local template
cp .env.example .env.local

# Edit with your values
nano .env.local

# Push all to Vercel
vercel env pull
```

Or set them one by one:

```bash
# Set for production
vercel env add GITHUB_ID production
vercel env add GITHUB_SECRET production
vercel env add NEXTAUTH_SECRET production
vercel env add OPENAI_API_KEY production
vercel env add RESEND_API_KEY production
vercel env add RESEND_FROM_EMAIL production
vercel env add CRON_SECRET production
vercel env add NEXTAUTH_URL production
```

## Deploy!

```bash
# Deploy to production
vercel --prod

# Your app is now live at:
# https://taskmaster-pro-xyz.vercel.app
```

## Verification Checklist

After deployment, verify all connections work:

### Database
```bash
# Test database connection
vercel logs --production
# Look for successful Prisma queries
```

### Authentication
1. Visit your app
2. Click "Sign in with GitHub"
3. Authorize the app
4. Should redirect back and be logged in

### AI Features
1. Create a task
2. Click "Get AI Suggestions"
3. Should see AI-generated suggestions

### File Upload
1. Upload an attachment to a task
2. Should see file URL
3. File should be accessible

### Email (test in development)
```bash
# Run the cron job manually
curl http://localhost:3000/api/cron/task-reminders \
  -H "Authorization: Bearer your-cron-secret"

# Check Resend dashboard for sent emails
```

### Cron Jobs
- Wait 24 hours for automatic execution
- Or check Vercel deployment logs: "Cron" tab

## Troubleshooting

### "Database connection failed"
```bash
# Check DATABASE_URL is set
vercel env ls

# Re-run migrations
npx prisma db push
```

### "GitHub OAuth failed"
- Verify callback URL matches exactly
- Check GITHUB_ID and GITHUB_SECRET are set
- Make sure NEXTAUTH_URL matches your domain

### "OpenAI rate limit exceeded"
- Set usage limits in OpenAI dashboard
- Consider caching AI responses
- Use gpt-4o-mini for lower costs

### "Email not sending"
- Verify RESEND_API_KEY is correct
- Check email logs in Resend dashboard
- Verify FROM email domain if using custom domain

### "Cron job not running"
- Check vercel.json has correct cron schedule
- Verify CRON_SECRET is set
- Check "Cron" tab in Vercel deployment for logs

## For Claude Code

When asking Claude Code to deploy or modify this app, provide this context:

> "This Next.js app deploys to Vercel (`vercel --prod`). It connects to:
> - Vercel Postgres (database)
> - GitHub OAuth (authentication)
> - OpenAI API (AI features)
> - Vercel Blob (file storage)
> - Resend (emails)
>
> All environment variables are set in Vercel. Run `npm run dev` locally,
> `vercel --prod` to deploy."

Claude Code will then understand the complete infrastructure and know how to work with it.

## Cost Monitoring

| Service | Free Tier | When You'll Hit Limits |
|---------|-----------|------------------------|
| Vercel | 100 GB bandwidth | ~100k visits/month |
| Postgres | 60 hours compute | ~2-3k users |
| Blob | 1 GB storage | ~10k files |
| OpenAI | None | $5-10/month light usage |
| Resend | 100 emails/day | ~3k emails/month |

**Expected monthly cost for small app**: $5-15/month

## Next Steps

1. ✅ Set up all accounts
2. ✅ Configure all environment variables
3. ✅ Deploy with `vercel --prod`
4. ✅ Test all integrations
5. 🚀 Build your app!

Now you have a complete, production-ready infrastructure. Claude Code knows exactly where everything is and how it connects!
