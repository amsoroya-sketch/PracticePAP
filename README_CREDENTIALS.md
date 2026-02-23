# Credentials Setup

## 🔒 Security Notice

This project uses **environment variables** to store sensitive credentials. Never commit credentials to Git!

---

## ⚙️ Setup Instructions

### **1. Create `.env` file**

Copy the example and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
ORG_URL=https://yourorg.crm6.dynamics.com
```

### **2. Verify `.env` is in `.gitignore`**

The `.env` file should NEVER be committed to Git. Verify:

```bash
cat .gitignore | grep .env
```

You should see:
```
.env
.env.local
.env.*.local
```

### **3. Test the setup**

Run any Python script to verify it works:

```bash
python3 validate_folder_url_patterns.py
```

If you see authentication errors, check that your `.env` file has the correct credentials.

---

## 📝 How It Works

All Python scripts import credentials from `config.py`:

```python
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL
```

The `config.py` module automatically loads credentials from `.env` file.

---

## 🚨 What NOT to Do

❌ **Never** commit `.env` file to Git
❌ **Never** hardcode credentials in Python files
❌ **Never** share your `.env` file or credentials

---

## ✅ What to Do

✅ Keep `.env` file local only
✅ Use environment variables in production
✅ Rotate secrets regularly
✅ Use different credentials for dev/prod

---

## 🔑 Getting Credentials

### **Azure AD Application Registration:**

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Create or select your application
4. Copy:
   - **Application (client) ID** → `CLIENT_ID`
   - **Directory (tenant) ID** → `TENANT_ID`
5. Go to **Certificates & secrets**
6. Create a new client secret → `CLIENT_SECRET`

### **Dataverse Organization URL:**

1. Go to [Power Platform Admin Center](https://admin.powerplatform.microsoft.com)
2. Select your environment
3. Copy the **Environment URL** → `ORG_URL`
   - Example: `https://org3a2a4fe5.crm6.dynamics.com`

---

## 🛠️ Troubleshooting

### **"ModuleNotFoundError: No module named 'config'"**

Make sure you're running the script from the project directory:

```bash
cd /path/to/PracticePAP
python3 script.py
```

### **"AttributeError: 'NoneType' object has no attribute..."**

Your `.env` file is missing or has incorrect values. Verify:

```bash
cat .env
```

Ensure all variables are set (no empty values).

---

## 📚 References

- [Azure AD App Registration](https://docs.microsoft.com/azure/active-directory/develop/quickstart-register-app)
- [Dataverse Web API](https://docs.microsoft.com/powerapps/developer/data-platform/webapi/overview)
- [GitHub Secret Scanning](https://docs.github.com/code-security/secret-scanning)

---

**Last Updated:** 2026-02-23
