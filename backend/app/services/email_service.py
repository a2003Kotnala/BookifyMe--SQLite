import logging

class EmailService:
    def __init__(self):
        # Default configuration - will be updated when app is available
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.smtp_username = None
        self.smtp_password = None
        self.from_email = 'noreply@bookifyme.com'
    
    def init_app(self, app):
        """Initialize the email service with app configuration"""
        self.smtp_server = app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = app.config.get('SMTP_PORT', 587)
        self.smtp_username = app.config.get('SMTP_USERNAME')
        self.smtp_password = app.config.get('SMTP_PASSWORD')
        self.from_email = app.config.get('FROM_EMAIL', 'noreply@bookifyme.com')
    
    def send_password_reset_email(self, user_email, reset_token):
        try:
            reset_link = f"http://localhost:5500/#reset-password?token={reset_token}"
            
            print("🔐 PASSWORD RESET REQUEST")
            print(f"📧 Email: {user_email}")
            print(f"🔗 Reset Link: {reset_link}")
            print("💡 Copy this link and open it in your browser to reset your password.")
            print("⏰ This link expires in 1 hour.")
            print("=" * 60)
            
            logging.info(f"Password reset token for {user_email}: {reset_token}")
            return True
            
        except Exception as e:
            logging.error(f"Error in email service: {e}")
            return True

# Create a global instance
email_service = EmailService()