# Spamhaus IP Removal Guide

Your logs show that your IP (`210.18.169.176`) is blocked by **Spamhaus**. This is why Outlook/Hotmail shows `ProviderProtected`, as they use Spamhaus to filter connections.

## How to Delist your IP

### 1. Identify the List
Visit the [Spamhaus IP Checker](https://check.spamhaus.org/) and enter your IP: `210.18.169.176`.
Commonly, you will be on the:
- **PBL (Policy Block List)**: This is normal for residential IPs. It means "this IP should not send mail directly."
- **SBL/XBL**: This means your IP was caught actually sending spam or has a virus.

### 2. Request Removal
1. Click on the listing link provided by the search result.
2. Look for the **"Request Removal"** or **"Delisting"** button.
3. Fill in your details. 
   - **Tip**: State that you are a student/developer building a validator and not sending bulk mail.
4. Confirm the email they send you.

### 3. Wait for Propagation
Spamhaus updates quickly (minutes), but mail servers like Outlook/Hotmail might cache the old list for **2 to 24 hours**.

---

## Why Google works but Outlook doesn't?
- **Google (Gmail)**: Uses its own massive internal data to decide who to block. They are often more lenient with residential IPs if the "handshake" looks legitimate.
- **Microsoft (Outlook/Hotmail)**: Relies heavily on third-party lists like Spamhaus. If you are on the PBL, Microsoft will block you instantly with a `5.7.1 Service unavailable` error.

---

## The Ultimate Solution
If you want **100% accurate results** for all domains, you SHOULD NOT use your local home/office internet.

### Recommended Steps:
1. **Get a VPS**: Use Kamatera, DigitalOcean, or Vultr. 
2. **Open Port 25**: Ask their support to "Open Outbound Port 25 for a legitimate email validation tool."
3. **Clean IP**: VPS IPs are in "Data Center" ranges, which are trusted more than "Residential" IPs.
