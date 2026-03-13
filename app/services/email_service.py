from datetime import datetime
import resend
from app.core.config import settings
from app.models.models import AlertType, Match, User
from app.core.logger import get_logger

resend.api_key = settings.RESEND_API_KEY

logger = get_logger(__name__)


# Alert type → human-readable label
ALERT_LABELS: dict[AlertType, str] = {
    AlertType.ONE_WEEK: "1 week",
    AlertType.THREE_DAYS: "3 days",
    AlertType.SIX_HOURS: "6 hours",
}


def _format_kickoff(kickoff_utc: datetime) -> str:
    return kickoff_utc.strftime("%A, %d %B %Y at %H:%M UTC")


def _build_email_html(match: Match, alert_type: AlertType, user: User) -> str:
    label = ALERT_LABELS[alert_type]
    kickoff_str = _format_kickoff(match.kickoff_utc)
    name = user.full_name or user.email.split("@")[0]

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">⚽ Match Reminder</h1>
        <p style="margin: 4px 0 0; opacity: 0.8;">{match.league_name}</p>
      </div>

      <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
        <p>Hi {name},</p>

        <p>A match you follow is happening in <strong>{label}</strong>:</p>

        <div style="background: white; border: 2px solid #e8e8e8; border-radius: 8px;
                    padding: 20px; text-align: center; margin: 20px 0;">
          <div style="display: flex; justify-content: space-around; align-items: center;">
            <div>
              <p style="font-size: 20px; font-weight: bold; margin: 0;">{match.home_team_name}</p>
              <p style="color: #666; margin: 4px 0 0;">Home</p>
            </div>
            <div style="font-size: 28px; color: #1a1a2e; font-weight: bold;">VS</div>
            <div>
              <p style="font-size: 20px; font-weight: bold; margin: 0;">{match.away_team_name}</p>
              <p style="color: #666; margin: 4px 0 0;">Away</p>
            </div>
          </div>
          <hr style="margin: 16px 0; border: none; border-top: 1px solid #eee;">
          <p style="margin: 0; color: #444;">🕐 {kickoff_str}</p>
          {"<p style='margin: 4px 0 0; color: #666;'>Matchday " + str(match.matchday) + "</p>" if match.matchday else ""}
        </div>

        <p style="color: #888; font-size: 12px; margin-top: 30px;">
          You're receiving this because you subscribed to alerts for
          <strong>{match.league_name}</strong> or one of these teams.
          <br>
          To manage your subscriptions, visit your account settings.
        </p>
      </div>
    </body>
    </html>
    """


async def send_match_alert(user: User, match: Match, alert_type: AlertType) -> bool:
    """
    Sends a match reminder email to the user.
    Returns True on success, False on failure.
    """
    label = ALERT_LABELS[alert_type]
    subject = (
        f"⚽ {match.home_team_name} vs {match.away_team_name} — Kicks off in {label}!"
    )
    logger.info(f"Sending '{label}' alert to {user.email} for match {match.id}")
    try:
        resend.Emails.send(
            {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                "to": [user.email],
                "subject": subject,
                "html": _build_email_html(match, alert_type, user),
            }
        )
        logger.info(
            f"[app.service.send_match_alert] Successfully sent '{label}' alert to {user.email} for match {match.id}"
        )
        return True
    except Exception as exc:
        # In production you'd log this properly
        logger.error(f"Failed to send to {user.email}: {exc}")
        return False
