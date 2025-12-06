# backend/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

# Email configuration (update with your actual email settings)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"  # Use app-specific password for Gmail
SENDER_NAME = "Air Quality Monitor"


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email with HTML content."""
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        message["To"] = to_email

        # Attach HTML content
        part = MIMEText(html_content, "html")
        message.attach(part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())

        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return False


def send_notification_email(user_email: str, aqi: float, category: str, risk_level: str) -> bool:
    """Send air quality notification email."""
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333; text-align: center;">🌍 Air Quality Alert</h2>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #f0f4f8; border-left: 4px solid #2563eb; border-radius: 4px;">
                    <p style="margin: 10px 0;"><strong>Current AQI:</strong> <span style="font-size: 24px; color: #2563eb;">{aqi:.1f}</span></p>
                    <p style="margin: 10px 0;"><strong>Category:</strong> <span style="font-weight: bold; color: #ef4444;">{category}</span></p>
                    <p style="margin: 10px 0;"><strong>Risk Level:</strong> <span style="color: #f59e0b;">{risk_level}</span></p>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #f9fafb; border-radius: 4px;">
                    <h3 style="color: #333; margin-top: 0;">Health Recommendations:</h3>
                    <ul style="color: #666; line-height: 1.8;">
                        <li>Check current air quality conditions in your area</li>
                        <li>Limit outdoor activities if AQI is high</li>
                        <li>Use air purifiers indoors if available</li>
                        <li>Wear N95 masks for outdoor activities if necessary</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; text-align: center; color: #999; font-size: 12px;">
                    <p>This is an automated notification from Air Quality Monitor</p>
                    <p><a href="http://127.0.0.1:8000" style="color: #2563eb; text-decoration: none;">View Dashboard</a></p>
                </div>
            </div>
        </body>
    </html>
    """
    return send_email(user_email, "🌍 Air Quality Alert", html_content)


def send_welcome_email(user_email: str, username: str) -> bool:
    """Send welcome email to new user."""
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Welcome to Air Quality Monitor, {username}! 👋</h2>
                
                <p style="color: #666; line-height: 1.6;">
                    Thank you for registering. You will now receive hourly air quality notifications.
                </p>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px;">
                    <h3 style="color: #10b981; margin-top: 0;">What to expect:</h3>
                    <ul style="color: #666; line-height: 1.8;">
                        <li>Hourly air quality updates via email</li>
                        <li>Real-time monitoring dashboard</li>
                        <li>AQI trends and historical data</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <a href="http://127.0.0.1:8000" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>
            </div>
        </body>
    </html>
    """
    return send_email(user_email, "Welcome to Air Quality Monitor", html_content)
