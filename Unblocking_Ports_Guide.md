# Guide: How to Unblock SMTP Ports (25, 587, 465)

If your "Network Diagnostic" shows that all ports are **BLOCKED**, it means something is stopping your computer from talking to the outside world. This can be at 3 levels: **Your PC**, **Your Router**, or **Your ISP**.

## Level 1: Your Windows PC (Firewall)
Windows might be blocking the Outbound connection.
1.  **Windows Firewall**:
    - Open "Windows Defender Firewall with Advanced Security".
    - Click **Outbound Rules**.
    - Click **New Rule**.
    - Choose **Port**, then **TCP**.
    - Specific remote ports: `25, 465, 587, 2525`.
    - Choose **Allow the connection**.
    - Name it "Email Validator Outbound".
2.  **Antivirus**: If you have Avast, Norton, or McAfee, they often have an "Email Shield" that blocks port 25. Try disabling it for 5 minutes to test.

## Level 2: Your Hardware (Router/Hotspot)
If you are using a WiFi router or a Mobile Hotspot, the hardware itself might have a firewall.
- **Router Settings**: Log in to your router (usually `192.168.1.1`) and look for "Firewall" or "Port Filtering" settings.
- **Mobile Hotspot**: Most mobile carriers (Jio, Airtel, etc.) **permanently block** Port 25 on mobile data to prevent spam. You cannot unblock this yourself.

## Level 3: Your Internet Provider (ISP) - Most Likely
Many ISPs block Port 25 by default.
- **Why?** To stop botnets from sending spam from home computers.
- **How to fix?** You can call your ISP's customer support and ask: *"Can you please unblock Port 25 for my account? I am a developer and need it for testing."*

---

## The "True" Solution (The Professional Way)
If you cannot unblock your local ports, you should not struggle with your ISP. Instead, do what the pros do:

### 1. Use an External SMTP Relay
Instead of "Probing" directly, you can use a service like **SendGrid**, **Mailgun**, or **Amazon SES**. They use Port 587 (which is usually open) and have clean reputations.

### 2. Move to a Cloud VPS
Rent a $5/month Linux server (DigitalOcean / Vultr). 
- These servers are designed for this.
- You can ask their support to "Open SMTP ports" and they will say YES once you verify your identity.

> [!IMPORTANT]
> If your Diagnostic shows **ALL** ports are red, it is 99% certain that your **ISP (Internet Service Provider)** is blocking you. Switching to a different type of internet (e.g., from Mobile Data to Home Fiber) is the fastest way to test this.
