# Publishing Guide: PyPI & npm

This guide walks you through publishing the LLMObserve SDK to PyPI (Python) and npm (JavaScript) so users can install via `pip install llmobserve` and `npm install llmobserve`.

---

## 📦 Part 1: PyPI (Python Package Index)

### Step 1: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Create an account (username, email, password)
3. **Verify your email** (check spam folder)
4. Enable **2FA** (Two-Factor Authentication) - **REQUIRED** for publishing
   - Go to Account Settings → Enable 2FA
   - Use an authenticator app (Google Authenticator, Authy, etc.)

### Step 2: Create API Token

1. Go to https://pypi.org/manage/account/token/
2. Click **"Add API token"**
3. Name it: `llmobserve-publish` (or whatever you want)
4. **Scope:** Select **"Entire account"** (or just the project if you prefer)
5. Click **"Add token"**
6. **COPY THE TOKEN** - it looks like `pypi-AgEIc...` (you won't see it again!)

### Step 3: Configure Local Environment

```bash
# Install build tools
pip install build twine

# Create .pypirc file in your home directory
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-AgEIc...YOUR_TOKEN_HERE
EOF

# Make it readable only by you
chmod 600 ~/.pypirc
```

**OR** use environment variable (more secure):

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIc...YOUR_TOKEN_HERE
```

### Step 4: Update Version Number

Before publishing, update the version in:
- `sdk/python/pyproject.toml` → `version = "0.3.0"`
- `sdk/python/setup.py` → `version="0.3.0"`

**Version format:** `MAJOR.MINOR.PATCH` (e.g., `0.3.0`, `0.3.1`, `1.0.0`)

### Step 5: Build and Publish

```bash
cd sdk/python

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Check the build (optional)
twine check dist/*

# Upload to PyPI (test first!)
twine upload --repository testpypi dist/*

# If test works, upload to real PyPI
twine upload dist/*
```

**Test PyPI:** https://test.pypi.org/ (use this first to verify everything works)

### Step 6: Verify Installation

```bash
# Wait ~5 minutes for PyPI to index
pip install llmobserve

# Or install specific version
pip install llmobserve==0.3.0
```

---

## 📦 Part 2: npm (Node Package Manager)

### Step 1: Create npm Account

1. Go to https://www.npmjs.com/signup
2. Create an account (username, email, password)
3. **Verify your email** (check spam folder)
4. Enable **2FA** (Two-Factor Authentication) - **REQUIRED** for publishing
   - Go to Account Settings → Enable 2FA
   - Use an authenticator app

### Step 2: Login to npm

```bash
# Login via CLI
npm login

# Enter:
# - Username: your-npm-username
# - Password: your-password
# - Email: your-email@example.com
# - OTP: (from 2FA app)

# Verify you're logged in
npm whoami
```

### Step 3: Update Version Number

Before publishing, update the version in:
- `sdk/js/package.json` → `"version": "0.2.0"`

**Version format:** `MAJOR.MINOR.PATCH` (e.g., `0.2.0`, `0.2.1`, `1.0.0`)

### Step 4: Build and Publish

```bash
cd sdk/js

# Clean previous builds
rm -rf dist/ node_modules/.cache/

# Build the package (TypeScript → JavaScript)
npm run build

# Test locally (optional)
npm pack
# This creates llmobserve-0.2.0.tgz - you can test installing it

# Publish to npm
npm publish

# If you want to publish as a beta/pre-release:
npm publish --tag beta
```

### Step 5: Verify Installation

```bash
# Wait ~2 minutes for npm to index
npm install llmobserve

# Or install specific version
npm install llmobserve@0.2.0
```

---

## 🔄 Updating Versions

### Semantic Versioning

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

### Update Process

1. **Update version numbers:**
   - Python: `sdk/python/pyproject.toml` and `sdk/python/setup.py`
   - JavaScript: `sdk/js/package.json`

2. **Commit and tag:**
   ```bash
   git add sdk/python/pyproject.toml sdk/python/setup.py sdk/js/package.json
   git commit -m "Bump version to 0.3.1"
   git tag v0.3.1
   git push origin main --tags
   ```

3. **Publish:**
   - Python: `cd sdk/python && python -m build && twine upload dist/*`
   - JavaScript: `cd sdk/js && npm run build && npm publish`

---

## 🚨 Common Issues

### PyPI

**"Package name already taken"**
- The name `llmobserve` might be taken. Check: https://pypi.org/project/llmobserve/
- If taken, use a different name or contact the owner

**"Invalid credentials"**
- Make sure you're using `__token__` as username and the full token as password
- Token must start with `pypi-`

**"2FA required"**
- You MUST enable 2FA on PyPI to publish
- Use an authenticator app, not SMS

### npm

**"Package name already taken"**
- Check: https://www.npmjs.com/package/llmobserve
- If taken, use a scoped package: `@llmobserve/sdk` (update package.json `name` field)

**"You must verify your email"**
- Check your email for verification link
- Or resend: https://www.npmjs.com/email-verify

**"2FA required"**
- You MUST enable 2FA on npm to publish
- Use an authenticator app

---

## 📝 Pre-Publish Checklist

- [ ] Version numbers updated in all files
- [ ] README.md is up to date
- [ ] Code is tested and working
- [ ] No sensitive data (API keys, tokens) in code
- [ ] License file included (MIT)
- [ ] `.gitignore` excludes `dist/`, `build/`, `*.egg-info/`
- [ ] PyPI account created + 2FA enabled
- [ ] npm account created + 2FA enabled
- [ ] Test publish to TestPyPI first
- [ ] Test install: `pip install llmobserve` and `npm install llmobserve`

---

## 🎯 Quick Commands Reference

### Python (PyPI)
```bash
cd sdk/python
python -m build
twine upload dist/*
```

### JavaScript (npm)
```bash
cd sdk/js
npm run build
npm publish
```

---

## 🔗 Useful Links

- **PyPI:** https://pypi.org/
- **Test PyPI:** https://test.pypi.org/
- **npm:** https://www.npmjs.com/
- **PyPI Account:** https://pypi.org/manage/account/
- **npm Account:** https://www.npmjs.com/settings/YOUR_USERNAME/packages

---

## 💡 Pro Tips

1. **Always test on TestPyPI first** before publishing to real PyPI
2. **Use semantic versioning** - don't jump from 0.1.0 to 2.0.0
3. **Write good release notes** - users want to know what changed
4. **Monitor downloads** - PyPI and npm both show download stats
5. **Keep versions in sync** - Python and JS should have similar version numbers (but don't have to match exactly)

