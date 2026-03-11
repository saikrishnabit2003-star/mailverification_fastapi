# Ngrok Setup Guide

To expose your Email Validator to the internet 24/7 with a persistent link, follows these steps.

## 1. Get an Ngrok Account & AuthToken
1.  Go to [ngrok.com](https://ngrok.com/) and sign up for a free account.
2.  Go to the **Dashboard** > **Your Authtoken** and copy your token.
3.  (Optional but Recommended) Go to **Cloud Edge** > **Domains** and claim your **one free static domain** (e.g., `yourname.ngrok-free.app`).

## 2. Option A: Manual Setup (Easiest)
If you just want to run it from your command line:
1.  Download and install ngrok on your Windows machine.
2.  Open your terminal and run:
    ```powershell
    ngrok config add-authtoken <YOUR_TOKEN>
    ```
3.  While your Docker app is running on port **8501**, run:
    ```powershell
    ngrok http 8501
    ```
    *If you have a static domain:*
    ```powershell
    ngrok http 8501 --domain=YOUR_DOMAIN.ngrok-free.app
    ```

## 3. Option B: Automated Docker Setup (Persistent)
To make Ngrok run automatically inside Docker, update your `docker-compose.yml`.

### Step 1: Create a `.env` file
Create a file named `.env` in the same folder as `docker-compose.yml` and add:
```env
NGROK_AUTHTOKEN=your_actual_token_here
NGROK_DOMAIN=your_static_domain_here.ngrok-free.app
```

### Step 2: Update `docker-compose.yml`
Add the `ngrok` service as shown below:

```yaml
services:
  email-validator:
    build: .
    ports:
      - "8501:7860"
    restart: always
    environment:
      - PYTHONUNBUFFERED=1

  ngrok:
    image: ngrok/ngrok:latest
    restart: always
    command:
      - "http"
      - "email-validator:7860"
      - "--domain=${NGROK_DOMAIN}"
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
    depends_on:
      - email-validator
```

## 4. Why Use a Static Domain?
Standard Ngrok links change every time you restart the service. By claiming a **Free Static Domain** on the Ngrok dashboard, your link will stay the same forever, which is perfect for a professional tool.
