DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "temp-mail.org", "10minutemail.com",
    "discard.email", "getnada.com", "owlymail.com", "maildrop.cc", "yopmail.com",
    "dispostable.com", "trashmail.com", "sharklasers.com", "guerrillamailblock.com",
    "guerrillamail.net", "guerrillamail.org", "guerrillamail.biz", "spam4.me",
    "grr.la", "pokemail.net", "vmani.com"
}

ROLE_NAMES = {
    "info", "support", "admin", "sales", "contact", "webmaster", "postmaster",
    "hostmaster", "marketing", "billing", "help", "noreply", "no-reply"
}

STATUS_MAP = {
    "Success": ("delivery", "mailboxExists"),
    "MailboxDoesNotExist": ("undelivery", "mailboxdoesnotexists"),
    "MailboxFull": ("delivery", "mailboxFull"),
    "GlobalCatchAll": ("Risky", "catchAllCharacterized"),
    "Disposable": ("undelivery", "isDisposable"),
    "InvalidSyntax": ("undelivery", "invalidCharacterInLocalPart"),
    "DnsError": ("Risky", "DnsError"),
    "SmtpConnectionTimeout": ("Risky", "smtpConnectionTimeout"),
    "LocalProbeBlocked": ("Risky", "localProbeBlocked"),
    "ProviderProtected": ("Risky", "providerProtected"),
    "SmtpError": ("Risky", "smtpError")
}
