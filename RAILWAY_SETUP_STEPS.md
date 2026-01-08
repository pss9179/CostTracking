# Railway CLI Setup Steps

## ✅ Step 1: Railway CLI Installed

Railway CLI has been successfully installed via Homebrew!

## 🔐 Step 2: Login to Railway

**Run this command in your terminal:**

```bash
railway login
```

This will:
1. Open your browser automatically
2. Ask you to authenticate with Railway
3. Complete the login process

**After logging in**, you should see a message like:
```
✓ Logged in as your-email@example.com
```

## 🔗 Step 3: Link to Your Railway Project

Once logged in, navigate to the collector directory and link to your Railway project:

```bash
cd collector
railway link
```

This will:
1. Show you a list of your Railway projects
2. Ask you to select the project (or create a new one)
3. Link your local directory to that project

**If you have multiple services**, you may also need to select a service:

```bash
railway service
```

## ✅ Step 4: Verify Setup

Check that everything is linked correctly:

```bash
# Check your Railway account
railway whoami

# Check linked project
railway status

# View environment variables (if any are set)
railway variables
```

## 🚀 Step 5: Ready for Testing!

Once you've completed these steps, let me know and we'll proceed with running the comprehensive platform tests!

---

## Quick Reference Commands

```bash
# Login
railway login

# Link to project
cd collector
railway link

# Select service (if multiple)
railway service

# View logs
railway logs

# Get deployment URL
railway domain

# Set environment variables
railway variables set KEY=value

# View all variables
railway variables
```



