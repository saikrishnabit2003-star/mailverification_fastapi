import smtplib
import socket
import dns.resolver
from email_validator import validate_email, EmailNotValidError
import random
import string
import threading
import time
from resources import DISPOSABLE_DOMAINS, ROLE_NAMES, STATUS_MAP

class EmailValidator:
    def __init__(self, timeout=7, sender_email="verify@gmail.com", rate_limit_delay=0.05):
        self.timeout = timeout
        self.sender_email = sender_email
        self.rate_limit_delay = rate_limit_delay
        self.last_check_time = 0
        self._lock = threading.Lock()

    def validate(self, email):
        # 0. Non-Blocking Rate Limiting
        wait_time = 0
        with self._lock:
            now = time.time()
            elapsed = now - self.last_check_time
            if elapsed < self.rate_limit_delay:
                wait_time = self.rate_limit_delay - elapsed
                self.last_check_time = now + wait_time
            else:
                self.last_check_time = now
        
        if wait_time > 0:
            time.sleep(wait_time)

        result = {
            "email": email,
            "classification": "Unknown",
            "status": "Attempted",
            "is_syntax_valid": False,
            "is_disposable": False,
            "is_role_based": False,
            "mx_records": [],
            "smtp_log": [],
            "domain": "",
            "provider": "Other"
        }

        # 1. Syntax Check
        try:
            valid = validate_email(email, check_deliverability=False)
            result["email"] = valid.normalized
            result["is_syntax_valid"] = True
            domain = valid.domain
            result["domain"] = domain
            local_part = valid.local_part
        except EmailNotValidError as e:
            self._set_status(result, "InvalidSyntax")
            result["smtp_log"].append(f"Syntax Error: {str(e)}")
            return result

        # 2. Disposable & Role Check
        if domain.lower() in DISPOSABLE_DOMAINS:
            result["is_disposable"] = True
            self._set_status(result, "Disposable")
        
        if local_part.lower() in ROLE_NAMES:
            result["is_role_based"] = True

        # 3. DNS & SMTP with 4x Retry Loop
        max_retries = 4
        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                result["smtp_log"].append(f"Auto-Retry {attempt}/{max_retries}...")
                time.sleep(0.5) # Small stabilization delay

            # DNS/MX Lookup
            try:
                mx_records = self._get_mx_records(domain)
                result["mx_records"] = mx_records
                if not mx_records:
                    self._set_status(result, "DnsError")
                    result["smtp_log"].append("No MX records found.")
                    # MX missing is usually not a transient error, but we'll retry anyway per request
                else:
                    # Detect Provider
                    mx_string = " ".join(mx_records).lower()
                    if "outlook.com" in mx_string or "protection.outlook.com" in mx_string:
                        result["provider"] = "outlook"
                    elif "google.com" in mx_string or "googlemail.com" in mx_string:
                        result["provider"] = "google"
                    else:
                        result["provider"] = "Other"

                    # 4. SMTP Handshake
                    self._check_smtp(result, domain, mx_records)

            except Exception as e:
                self._set_status(result, "DnsError")
                result["smtp_log"].append(f"DNS Lookup Error: {str(e)}")

            # Check if we should stop retrying
            # We ONLY retry if it's DnsError or SmtpError (transient)
            if result["status"] not in ["DnsError", "smtpError", "smtpConnectionTimeout"]:
                break
            
        return result

    def _get_mx_records(self, domain):
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_list = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in records])
            return [x[1] for x in mx_list]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            return []

    def _check_smtp(self, result, domain, mx_records):
        email = result["email"]
        ports = [25, 587, 2525] # Try standard and common submission ports
        best_mx = mx_records[0]
        
        success = False
        last_error = ""

        for port in ports:
            try:
                result["smtp_log"].append(f"Attempting connection to {best_mx}:{port}...")
                with smtplib.SMTP(best_mx, port, timeout=self.timeout) as smtp:
                    smtp.set_debuglevel(0)
                    smtp.ehlo(socket.gethostname())
                    if smtp.has_extn('STARTTLS'):
                        try:
                            smtp.starttls()
                            smtp.ehlo(socket.gethostname())
                        except Exception:
                            pass # STARTTLS failure isn't always fatal
                    
                    smtp.mail(self.sender_email)
                    code, msg = smtp.rcpt(email)
                    
                    msg_text = msg.decode('utf-8', 'ignore')
                    result["smtp_log"].append(f"Port {port} Success: {code} {msg_text}")
                    
                    if code == 250:
                        if self._is_catch_all(smtp, domain):
                            self._set_status(result, "GlobalCatchAll")
                        else:
                            self._set_status(result, "Success")
                        success = True
                    elif code == 550:
                        if any(k in msg_text.lower() for k in ["policy", "blocked", "reputation", "spam", "spamhaus"]):
                            result["smtp_log"].append("HEALER: Reputation block detected (Likely Deliverable).")
                            self._set_status(result, "ProviderProtected")
                        else:
                            self._set_status(result, "MailboxDoesNotExist")
                        success = True
                    elif code in [450, 451, 452]:
                        self._set_status(result, "MailboxFull")
                        success = True
                    
                    if success:
                        break # Stop if we got a definitive answer

            except (socket.timeout, TimeoutError):
                last_error = f"Timeout on port {port}"
                result["smtp_log"].append(last_error)
            except ConnectionRefusedError:
                last_error = f"Connection refused on port {port}"
                result["smtp_log"].append(last_error)
            except Exception as e:
                last_error = f"Error on port {port}: {str(e)}"
                result["smtp_log"].append(last_error)

        if not success:
            # HEALER LOGIC: Analyze WHY we failed
            error_lower = last_error.lower()
            
            if any(k in error_lower for k in ["spamhaus", "5.7.1", "policy", "reputation", "blocked", "unreachable", "101", "111", "refused", "timeout"]):
                result["smtp_log"].append(f"HEALER: Detected Network/Provider Block ({last_error}).")
                result["smtp_log"].append("HEALER: MX Records exist. Classifying as PROTECTED (Likely Deliverable).")
                self._set_status(result, "ProviderProtected")
            else:
                self._set_status(result, "SmtpError")

    def _is_catch_all(self, smtp, domain):
        random_user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
        fake_email = f"{random_user}@{domain}"
        code, _ = smtp.rcpt(fake_email)
        return code == 250

    def _set_status(self, result, status_key):
        classification, status_code = STATUS_MAP.get(status_key, ("Unknown", "Unknown"))
        result["classification"] = classification
        result["status"] = status_code

    def check_network_health(self):
        """Tests if common SMTP ports are open on the current host."""
        test_host = "google-main.mx.google.com" # Reliable host for testing
        results = {}
        for port in [25, 465, 587, 2525]:
            try:
                # Use a socket to test if we can reach the port
                with socket.create_connection((test_host, port), timeout=3):
                    results[port] = True
            except (socket.timeout, ConnectionRefusedError, OSError):
                results[port] = False
        return results
