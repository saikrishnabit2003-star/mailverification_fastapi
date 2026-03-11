# Understanding ProviderProtected Status

If your email validation result shows **Deliverable** but with the status **ProviderProtected**, it means the tool has successfully verified that the domain is real and has mail servers, but it was stopped from finishing the final handshake.

## What is happening?
The tool attempted to talk to the mail server (like Gmail or Outlook), but the server replied with:
- **A Reputation Block**: "Your IP is on a blacklist (Spamhaus, etc.)"
- **A Policy Block**: "We don't accept mail from residential connections."
- **A Network Timeout**: "I can't reach the server at all."

## Why is it classified as "Deliverable"?
Because of the **"Healer Logic"**. 
If a server says: *"I'm blocking you because I don't like your IP,"* it confirms that the server is active and the email domain exists. Professional tools like Verifalia use this logic to tell you the email is "Likely Deliverable" even if they are blocked.

## Why does it still show this even after changing network?
1. **Cached Data**: Sometimes Gmail/Outlook caches blocklists for a few hours. Even if you "clean" your IP, they might not see it yet.
2. **Multiple Lists**: You might be clean on Spamhaus, but on Barracuda, Sorbs, or Microsoft's internal list.
3. **ISP Policy**: Some mobile networks also block Port 25 by default to prevent spam.

## Why is Google accurate but Outlook isn't?
- **Microsoft (Outlook/Hotmail)** is extremely strict. They use **Spamhaus** as their primary gatekeeper. If your IP is on Spamhaus, Microsoft will block you immediately.
- **Google (Gmail)** is more sophisticated and uses internal reputation. If your connection looks "human" and follows all SMTP rules, they might let you through even if you are on some public blacklists.

## How to get 100% "MailboxExists" (Pure Green)?
1. **Wait**: If you just delisted your IP, wait for 2-4 hours.
2. **Professional Hosting**: Use a VPS (like DigitalOcean) and ask them to open Port 25.
3. **Clean Proxies**: Use a high-quality residential proxy.

> [!TIP]
> **ProviderProtected** is a "Safe" result. It means the email is almost certainly real, but your current internet connection is simply not "trusted" enough by big providers like Google to do a deeper check.
