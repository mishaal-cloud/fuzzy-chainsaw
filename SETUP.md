# Claude Code Development Setup Guide

This guide ensures Claude Code has everything needed to build, run, and deploy applications in this repository.

## The Problem This Solves

Without proper setup, Claude Code can write code but doesn't know:
- Where to run the application
- How to deploy it
- What the build process is
- Where dependencies are defined

This guide fixes that.

## Quick Start Setup

### Step 1: Choose Your Stack

Pick based on what you're building:

#### Option A: **Frontend/Fullstack Web App** (React, Vue, Next.js, etc.)
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link this project to Vercel
vercel link

# Deploy
vercel --prod
```

**Why Vercel?**
- Zero-config deployments
- Automatic HTTPS
- Global CDN
- Excellent free tier
- Works with: Next.js, React, Vue, Svelte, vanilla JS

#### Option B: **Backend API/Service** (Node.js, Python, Go, etc.)
```bash
# Install Railway CLI
npm install -g @railway/cli
# OR use Fly.io
curl -L https://fly.io/install.sh | sh

# Login
railway login  # or: fly auth login

# Initialize project
railway init   # or: fly launch

# Deploy
railway up     # or: fly deploy
```

**Why Railway/Fly?**
- Supports any language/framework
- Built-in database options
- Simple environment variables
- Great free tier

#### Option C: **Full Stack with Database**
```bash
# Use Vercel for frontend + Railway for backend
# Or use a monorepo with:
npm install -g vercel @railway/cli
```

### Step 2: Create Project Configuration

Always include these files so Claude Code understands your project:

#### For Node.js/JavaScript Projects:

**package.json**
```json
{
  "name": "fuzzy-chainsaw",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "deploy": "vercel --prod"
  },
  "dependencies": {},
  "devDependencies": {}
}
```

#### For Python Projects:

**requirements.txt**
```txt
fastapi==0.104.1
uvicorn==0.24.0
```

**railway.toml** or **fly.toml**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

### Step 3: Document Deployment in README

Update README.md with clear deployment instructions:

```markdown
## Development

\`\`\`bash
npm install
npm run dev
\`\`\`

## Deployment

This project is configured to deploy to [Vercel/Railway/Fly].

\`\`\`bash
# Deploy to production
npm run deploy
# or: vercel --prod
# or: railway up
# or: fly deploy
\`\`\`

## Environment Variables

Required environment variables:
- \`DATABASE_URL\` - PostgreSQL connection string
- \`API_KEY\` - External API key (if needed)
```

### Step 4: Set Up Environment Variables

Create `.env.example`:
```bash
# Database
DATABASE_URL=postgresql://localhost/mydb

# API Keys
API_KEY=your_api_key_here

# App Config
PORT=3000
NODE_ENV=development
```

Create `.env` (not committed):
```bash
cp .env.example .env
# Then fill in real values
```

Add to `.gitignore`:
```
.env
.env.local
node_modules/
dist/
.vercel
.railway
```

## Essential Project Structure

```
fuzzy-chainsaw/
├── README.md              # What the project is, how to run it
├── SETUP.md              # This file - how to set up infrastructure
├── package.json          # Dependencies and scripts (Node.js)
├── requirements.txt      # Dependencies (Python)
├── .env.example          # Environment variables template
├── .env                  # Actual secrets (git-ignored)
├── .gitignore            # What not to commit
├── vercel.json           # Vercel configuration (if using)
├── railway.toml          # Railway configuration (if using)
└── src/                  # Your application code
```

## Complete Example Setups

### Example 1: React + Vite + Vercel

```bash
# Initialize
npm create vite@latest . -- --template react
npm install

# Set up Vercel
vercel link

# Deploy
vercel --prod
```

**vercel.json:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

### Example 2: FastAPI + Railway

```bash
# Create main.py
cat > main.py << 'EOF'
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
EOF

# Deploy
railway init
railway up
```

### Example 3: Next.js Fullstack + Vercel + Vercel Postgres

```bash
# Initialize Next.js
npx create-next-app@latest . --typescript --tailwind --app

# Add Vercel Postgres
npm install @vercel/postgres

# Deploy
vercel link
vercel --prod
```

## Working with Claude Code

### Tell Claude Code Your Stack

When starting a new project, tell Claude Code:

> "I want to build a [React/Next.js/FastAPI] app. Set it up to deploy to [Vercel/Railway/Fly]. Include all necessary config files."

### Provide Context in Each Session

At the start of a session, remind Claude Code:

> "This project deploys to Vercel using `vercel --prod`. The build command is `npm run build`."

Or better yet, add this to your README.md so it's always visible.

### Use Clear Commands

Instead of: "Deploy this"
Say: "Run `vercel --prod` to deploy to production"

Instead of: "Make this work"
Say: "Install dependencies with `npm install` and run dev server with `npm run dev`"

## Recommended Stack Combinations

### For MVPs and Simple Apps
- **Frontend**: Vercel + React/Next.js
- **Backend**: Vercel API Routes (serverless)
- **Database**: Vercel Postgres
- **Total cost**: Free for most projects

### For Complex Apps
- **Frontend**: Vercel + Next.js
- **Backend**: Railway + Node.js/Python
- **Database**: Railway PostgreSQL
- **Total cost**: ~$5-10/month

### For Maximum Simplicity
- **Everything**: Next.js on Vercel (fullstack)
- **Database**: Vercel Postgres
- **Total cost**: Free tier available

## Troubleshooting

### "I don't know where to deploy"
**Fix**: Add deployment commands to package.json scripts and document in README

### "Dependencies not found"
**Fix**: Ensure package.json/requirements.txt is committed and up to date

### "Build failed"
**Fix**: Test build locally first: `npm run build` or `python -m pip install -r requirements.txt`

### "Environment variables missing"
**Fix**: Create .env.example, document all required variables in README

## Next Steps

1. **Choose your stack** from the options above
2. **Install the CLI tools** for your chosen platform
3. **Initialize and link** your project
4. **Create the config files** (package.json, vercel.json, etc.)
5. **Update README.md** with deployment instructions
6. **Test deployment** manually once to ensure it works
7. **Tell Claude Code** about your setup in future sessions

## Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Fly.io Documentation](https://fly.io/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

---

**Pro Tip**: Once you have this setup working for one project, you can use it as a template for all future projects. Just copy the config files and adjust as needed.
