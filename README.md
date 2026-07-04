# Identity Provisioning Engine

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Microsoft Entra ID](https://img.shields.io/badge/Microsoft%20Entra%20ID-Integrated-blue)](https://entra.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Automated user provisioning and role-based access control (RBAC) for Microsoft Entra ID using Python and the Microsoft Graph API.

## 🚀 What This Does

- 📋 Reads employee data from a CSV file
- 👤 Creates user accounts in Microsoft Entra ID
- 🔐 Assigns users to security groups based on department (RBAC)
- 📊 Generates audit reports and logs every action
- 🔍 Supports dry-run mode for safe testing
- 💪 Handles failures gracefully with retry logic

## 🛠️ Tech Stack

- **Python** 3.8+ – Core automation
- **Microsoft Entra ID** – Identity provider
- **Microsoft Graph API** – User/group management
- **MSAL** – OAuth 2.0 authentication
- **pandas** – CSV processing

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/identity-provisioning-engine.git
cd identity-provisioning-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your tenant ID, client ID, and secret
