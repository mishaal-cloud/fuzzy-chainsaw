# fuzzy-chainsaw
A short and memorable repository for project development

## For Claude Code Users: Start Here!

This repository is configured to work seamlessly with Claude Code. Before asking Claude Code to build anything, complete the setup:

### First Time Setup (5 minutes)

1. **Read the Quick Start**: [QUICKSTART.md](./QUICKSTART.md)
2. **Choose your stack** (React/Next.js/FastAPI/Express)
3. **Install CLI tools** (Vercel/Railway/Fly)
4. **Deploy once manually** to verify it works

### Comprehensive Guide

For detailed information about infrastructure setup, deployment options, and best practices:
- Read [SETUP.md](./SETUP.md) - Complete infrastructure guide

### Templates Available

Ready-to-use configuration files in `templates/`:
- `vercel-react-vite.json` - React + Vite + Vercel
- `vercel-nextjs.json` - Next.js + Vercel
- `railway-fastapi-requirements.txt` - FastAPI + Railway
- `railway-express.json` - Express + Railway
- `.env.example` - Environment variables template
- `.gitignore` - Standard ignore patterns

## Quick Reference

Once set up, tell Claude Code:

> "This is a [React/Next.js/FastAPI/Express] app that deploys to [Vercel/Railway] using `[deploy command]`"

Then ask Claude Code to build what you need!

## Common Commands

```bash
# Development
npm install          # Install dependencies
npm run dev          # Start dev server

# Deployment
npm run deploy       # Deploy to production
# or: vercel --prod
# or: railway up
# or: fly deploy
```

## Project Status

- [ ] Stack chosen (React/Next.js/FastAPI/Express)
- [ ] Platform configured (Vercel/Railway/Fly)
- [ ] CLI tools installed
- [ ] First manual deployment successful
- [ ] Ready to build with Claude Code!

---

**Remember**: Claude Code needs infrastructure set up before it can deploy. Complete the setup above, then Claude Code will know exactly where to run your code.
