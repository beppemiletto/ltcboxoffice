"""
Custom email backend that bypasses SSL certificate verification.
Only for development with test SMTP servers like imitate.email.
DO NOT USE IN PRODUCTION!
"""
import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class UnverifiedSSLEmailBackend(SMTPBackend):
    """
    Email backend that uses unverified SSL context.
    This bypasses SSL certificate verification issues with test SMTP servers.
    """

    def open(self):
        """
        Override open() to use unverified SSL context.
        """
        if self.connection:
            return False

        connection_params = {
            'timeout': self.timeout,
        }

        if self.use_ssl:
            # Create unverified SSL context for development
            connection_params['context'] = ssl._create_unverified_context()

        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            # TLS/STARTTLS
            if self.use_tls:
                self.connection.ehlo()
                self.connection.starttls(context=ssl._create_unverified_context())
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except Exception as e:
            if not self.fail_silently:
                raise
            return False
