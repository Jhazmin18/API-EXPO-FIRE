import ssl

from django.core.mail.backends.smtp import EmailBackend


class SafeSMTPEmailBackend(EmailBackend):
    """
    SMTP backend with an explicit SSL context.

    In some Windows/Conda environments, `ssl.create_default_context()`
    can fail while loading the system certificate store. For password
    reset emails we prefer a predictable context over crashing the request.
    """

    @property
    def ssl_context(self):
        if self._ssl_context is None:
            self._ssl_context = ssl._create_unverified_context()
        return self._ssl_context
