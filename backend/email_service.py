"""
Email Alert Service
Sends real SMTP email alerts for high-risk user activity.
Falls back gracefully if SMTP is not configured.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailAlertService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)

    def is_configured(self):
        """Check if SMTP credentials are set"""
        return bool(self.smtp_user and self.smtp_password)

    def send_email_alert(self, to_email, subject, body_text, body_html=None):
        """
        Send a generic email alert.

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body_text (str): Plain text body
            body_html (str): Optional HTML body

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_configured():
            print(
                "⚠️ SMTP not configured — email not sent. "
                "Set SMTP_USER and SMTP_PASSWORD in .env"
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            msg.attach(MIMEText(body_text, "plain"))
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            print(f"✅ Email alert sent to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP authentication failed — check SMTP_USER and SMTP_PASSWORD")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            print(f"❌ Email send failed: {e}")
            return False

    def send_high_risk_alert(self, user_id, risk_score, email):
        """
        Send a high-risk activity alert email.

        Args:
            user_id (str): The user who triggered the alert
            risk_score (float): The calculated risk score
            email (str): Recipient email address
        """
        if not email:
            print("⚠️ No alert email configured — skipping email alert")
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "LOCKED" if risk_score >= 80 else "HIGH RISK"

        subject = f"🚨 [{status}] User Behavior Alert — {user_id}"

        body_text = (
            f"SECURITY ALERT\n\n"
            f"User ID   : {user_id}\n"
            f"Risk Score: {risk_score:.1f} / 100\n"
            f"Status    : {status}\n"
            f"Timestamp : {now}\n\n"
            f"Please review this user's activity in the dashboard immediately."
        )

        body_html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0f172a;color:#f8fafc;padding:24px;">
          <div style="max-width:520px;margin:auto;background:#1e293b;border-radius:12px;
                      padding:28px;border:1px solid #ef4444;">
            <h2 style="color:#ef4444;margin-top:0;">🚨 {status} — Security Alert</h2>
            <table style="width:100%;border-collapse:collapse;">
              <tr>
                <td style="padding:8px 0;color:#94a3b8;width:40%;">User ID</td>
                <td style="padding:8px 0;font-weight:bold;">{user_id}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#94a3b8;">Risk Score</td>
                <td style="padding:8px 0;color:#ef4444;font-weight:bold;font-size:1.2em;">
                  {risk_score:.1f} / 100
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#94a3b8;">Status</td>
                <td style="padding:8px 0;">
                  <span style="background:#ef444420;color:#ef4444;padding:4px 10px;
                               border-radius:8px;font-weight:bold;">{status}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#94a3b8;">Timestamp</td>
                <td style="padding:8px 0;">{now}</td>
              </tr>
            </table>
            <p style="margin-top:20px;color:#94a3b8;font-size:0.9em;">
              Please review this user's activity in the UBA dashboard immediately.
            </p>
          </div>
        </body></html>
        """

        return self.send_email_alert(email, subject, body_text, body_html)


# Global instance
alert_service = EmailAlertService()
