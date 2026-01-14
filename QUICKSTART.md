# Quick Start Guide - Working with Claude Code

This guide gets you from zero to deployed in 10 minutes.

## Choose Your Path

### Path 1: Frontend App (Recommended for Beginners)

**What you'll get**: A React app deployed to Vercel

```bash
# 1. Copy the template
cp templates/vercel-react-vite.json package.json

# 2. Install dependencies
npm install

# 3. Create a basic React app with Vite
npm create vite@latest . -- --template react

# 4. Set up Vercel
npm install -g vercel
vercel login
vercel link

# 5. Deploy
npm run deploy
```

**Tell Claude Code**:
> "This is a React + Vite app that deploys to Vercel using `npm run deploy`"

---

### Path 2: Next.js Fullstack App

**What you'll get**: A Next.js app with API routes, deployed to Vercel

```bash
# 1. Create Next.js app
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# 2. Install Vercel CLI
npm install -g vercel
vercel login
vercel link

# 3. Deploy
vercel --prod
```

**Tell Claude Code**:
> "This is a Next.js fullstack app that deploys to Vercel using `vercel --prod`"

---

### Path 3: Python API

**What you'll get**: A FastAPI backend deployed to Railway

```bash
# 1. Copy template
cp templates/railway-fastapi-requirements.txt requirements.txt

# 2. Create a basic API
cat > main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
EOF

# 3. Install Railway CLI
npm install -g @railway/cli
railway login

# 4. Initialize and deploy
railway init
railway up
```

**Tell Claude Code**:
> "This is a FastAPI app that deploys to Railway using `railway up`"

---

### Path 4: Node.js API

**What you'll get**: An Express API deployed to Railway

```bash
# 1. Copy template
cp templates/railway-express.json package.json

# 2. Install dependencies
npm install

# 3. Create a basic API
cat > index.js << 'EOF'
import express from 'express';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Hello World' });
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
EOF

# 4. Deploy to Railway
npm install -g @railway/cli
railway login
railway init
railway up
```

**Tell Claude Code**:
> "This is an Express API that deploys to Railway using `npm run deploy`"

---

## After Initial Setup

### 1. Set up environment variables

```bash
# Copy the example
cp templates/.env.example .env

# Edit .env with your actual values
# (Never commit this file!)
```

### 2. Set up .gitignore

```bash
cp templates/.gitignore .gitignore
```

### 3. Update README.md

Add this to your README:

```markdown
## Development

\`\`\`bash
npm install        # Install dependencies
npm run dev        # Run development server
\`\`\`

## Deployment

This project deploys to [Vercel/Railway].

\`\`\`bash
npm run deploy     # Deploy to production
\`\`\`

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

\`\`\`bash
cp .env.example .env
\`\`\`

Required variables:
- `DATABASE_URL` - Database connection string
- `API_KEY` - External API key
```

### 4. Test locally

```bash
npm run dev
# Visit http://localhost:3000
```

### 5. Deploy manually once

```bash
npm run deploy
# or: vercel --prod
# or: railway up
```

### 6. Commit everything

```bash
git add .
git commit -m "Initial project setup with deployment configuration"
git push
```

## Working with Claude Code

### Starting a New Feature

Tell Claude Code clearly what you want:

> "I want to add a user authentication feature using JWT. This app deploys to Vercel with `npm run deploy`."

### When Claude Code Asks "Where Should I Deploy?"

Point to your README:

> "Check the README.md for deployment instructions. Use `npm run deploy`."

### If Something Doesn't Work

Ask Claude Code to check the configuration:

> "Check package.json and verify the build command is correct. Run `npm run build` to test locally first."

## Troubleshooting

### "Command not found: vercel/railway"

Install the CLI:
```bash
npm install -g vercel
# or
npm install -g @railway/cli
```

### "Deployment failed"

Test locally first:
```bash
npm run build    # Should complete without errors
npm run preview  # Should run the built app
```

### "Environment variables missing"

Set them in your platform:
```bash
# Vercel
vercel env add DATABASE_URL

# Railway
railway variables set DATABASE_URL=your-value
```

## Next Steps

1. Read [SETUP.md](./SETUP.md) for comprehensive setup guide
2. Choose your deployment platform and install CLI
3. Run through your chosen Quick Start path
4. Deploy manually once to verify it works
5. Start building with Claude Code!

---

**Remember**: Claude Code is excellent at writing code, but it needs you to set up the infrastructure first. Once you have these configurations in place, Claude Code will know exactly what to do.
