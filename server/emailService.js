const nodemailer = require('nodemailer');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

class EmailService {
  constructor() {
    this.refreshConfig();
  }

  refreshConfig() {
    this.devMode = process.env.DEV_EMAIL_MODE === 'true' ||
      (!process.env.SMTP_USER &&
        !process.env.RESEND_API_KEY &&
        !process.env.SENDGRID_API_KEY &&
        !process.env.BREVO_API_KEY);

    this.service = process.env.EMAIL_SERVICE || 'smtp';

    this.smtpHost = process.env.SMTP_HOST || 'localhost';
    this.smtpPort = parseInt(process.env.SMTP_PORT || '587', 10);
    this.smtpSecure = process.env.SMTP_SECURE === 'true';
    this.smtpUser = process.env.SMTP_USER || '';
    this.smtpPass = process.env.SMTP_PASS || '';

    this.brevoApiKey = process.env.BREVO_API_KEY || '';
    this.brevoSenderEmail = process.env.BREVO_SENDER_EMAIL || '';
    this.brevoSenderName = process.env.BREVO_SENDER_NAME || 'EVENTRA';

    this.fromEmail = process.env.EMAIL_FROM ||
      '"EVENTRA Security" <no-reply@eventra.com>';
  }

  isDevMode() {
    this.refreshConfig();
    return this.devMode;
  }

  getTransporter() {
    if (this.smtpUser && this.smtpPass) {
      return nodemailer.createTransport({
        host: this.smtpHost,
        port: this.smtpPort,
        secure: this.smtpSecure,
        auth: {
          user: this.smtpUser,
          pass: this.smtpPass
        }
      });
    }

    return null;
  }

  async sendViaBrevo({
    toEmail,
    displayName,
    otp,
    expiresMinutes,
    text,
    html
  }) {
    if (!this.brevoApiKey) {
      throw new Error('BREVO_API_KEY is not configured.');
    }

    if (!this.brevoSenderEmail) {
      throw new Error('BREVO_SENDER_EMAIL is not configured.');
    }

    const response = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'api-key': this.brevoApiKey,
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        sender: {
          name: this.brevoSenderName,
          email: this.brevoSenderEmail
        },
        to: [
          {
            email: toEmail,
            name: displayName
          }
        ],
        subject: `Your EVENTRA Password Reset Code: ${otp}`,
        textContent: text,
        htmlContent: html
      })
    });

    const responseText = await response.text();

    if (!response.ok) {
      throw new Error(
        `Brevo API ${response.status}: ${responseText}`
      );
    }

    let result = {};

    try {
      result = JSON.parse(responseText);
    } catch (_) {
      // Brevo may return an empty response body for some successful requests.
    }

    console.log(
      `[EMAIL] Reset OTP email dispatched to ${toEmail} via Brevo` +
      (result.messageId ? ` (MessageId: ${result.messageId})` : '')
    );

    return result;
  }

  async sendPasswordResetOtp({
    toEmail,
    userName,
    otp,
    expiresMinutes = 10
  }) {
    this.refreshConfig();

    const cleanEmail = (toEmail || '').trim().toLowerCase();
    const displayName = userName || 'Valued Member';

    if (this.devMode) {
      console.log('\n' + '='.repeat(76));
      console.log(' [DEV EMAIL MODE] 📧 EVENTRA PASSWORD RESET OTP');
      console.log('-'.repeat(76));
      console.log(` Recipient : ${cleanEmail} (${displayName})`);
      console.log(` OTP Code  : ${otp}`);
      console.log(` Validity  : ${expiresMinutes} minutes`);
      console.log(` Timestamp : ${new Date().toISOString()}`);
      console.log(' Notice    : Real email sending bypassed.');
      console.log('='.repeat(76) + '\n');

      return {
        success: true,
        mode: 'development',
        message: 'OTP logged to server console (Development Mode).'
      };
    }

    const text = `Hello ${displayName},

Your one-time password (OTP) for resetting your EVENTRA account password is: ${otp}

This OTP is valid for ${expiresMinutes} minutes and can only be used once.

If you did not request a password reset, please ignore this email or contact security support immediately.

Regards,
EVENTRA Security Team`;

    const html = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 560px; margin: 0 auto; background: #0f172a; color: #f8fafc; border-radius: 12px; overflow: hidden; border: 1px solid #334155;">
        <div style="background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%); padding: 24px; text-align: center;">
          <h1 style="margin: 0; color: #ffffff; font-size: 24px; letter-spacing: 1px;">EVENTRA</h1>
          <p style="margin: 6px 0 0; color: #e0e7ff; font-size: 13px;">Security & Account Authentication</p>
        </div>

        <div style="padding: 28px 24px;">
          <h2 style="margin: 0 0 12px; color: #ffffff; font-size: 18px;">
            Password Reset Verification
          </h2>

          <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 0 0 20px;">
            Hello <strong>${displayName}</strong>,<br>
            We received a request to reset the password for your EVENTRA account
            (<code>${cleanEmail}</code>).
            Use the verification code below to proceed:
          </p>

          <div style="text-align: center; margin: 24px 0;">
            <div style="display: inline-block; background: #1e293b; border: 2px dashed #6366f1; border-radius: 10px; padding: 14px 32px; font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #a5b4fc; font-family: monospace;">
              ${otp}
            </div>

            <p style="color: #64748b; font-size: 12px; margin-top: 10px;">
              Valid for ${expiresMinutes} minutes • Single-use only
            </p>
          </div>

          <p style="color: #94a3b8; font-size: 13px; line-height: 1.5; margin: 20px 0 0; border-top: 1px solid #1e293b; padding-top: 16px;">
            🔒 <strong>Security Notice:</strong>
            If you did not initiate this request, your account is still secure.
            You can safely disregard this email. Never share your OTP with anyone.
          </p>
        </div>

        <div style="background: #090d16; padding: 16px; text-align: center; font-size: 11px; color: #64748b;">
          © ${new Date().getFullYear()} EVENTRA Platform • Intelligent Event Management System
        </div>
      </div>
    `;

    try {
      // 1. Brevo HTTPS API
      // Used on Render Free because SMTP ports are blocked there.
      if (this.brevoApiKey && this.brevoSenderEmail) {
        await this.sendViaBrevo({
          toEmail: cleanEmail,
          displayName,
          otp,
          expiresMinutes,
          text,
          html
        });

        return {
          success: true,
          mode: 'brevo',
          message: 'OTP has been dispatched to your email address.'
        };
      }

      // 2. Existing SMTP fallback
      const transporter = this.getTransporter();

      if (!transporter) {
        throw new Error('Email provider configuration is incomplete.');
      }

      const mailOptions = {
        from: this.fromEmail,
        to: cleanEmail,
        subject: `Your EVENTRA Password Reset Code: ${otp}`,
        text,
        html
      };

      const info = await transporter.sendMail(mailOptions);

      console.log(
        `[EMAIL] Reset OTP email dispatched to ${cleanEmail} ` +
        `(MessageId: ${info.messageId})`
      );

      return {
        success: true,
        mode: 'smtp',
        message: 'OTP has been dispatched to your email address.'
      };

    } catch (error) {
      console.error(
        `[EMAIL ERROR] Failed to send email to ${cleanEmail}:`,
        error.message
      );

      return {
        success: false,
        error: 'Unable to deliver OTP email. Please verify email configuration.'
      };
    }
  }
}

module.exports = new EmailService();