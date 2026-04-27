import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration (To be filled by user for production)
SMTP_SERVER = os.getenv("LOGISPHERE_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("LOGISPHERE_SMTP_PORT", 587))
SMTP_USER = os.getenv("LOGISPHERE_SMTP_USER", "")
SMTP_PASS = os.getenv("LOGISPHERE_SMTP_PASS", "")

def send_risk_alert(risk_count, recommendations):
    """
    Sends an email alert if critical risks are detected.
    If no SMTP credentials are provided, it logs to a local file for demo.
    """
    subject = f"⚠️ ALERTE LOGISTIQUE : {risk_count} expéditions à HAUT RISQUE détectées"
    
    body = f"""
    Bonjour,
    
    Le Pipeline LogiSphere AI a détecté {risk_count} expéditions avec un niveau de risque ÉLEVÉ.
    
    🎯 RECOMMANDATIONS DE L'IA :
    ---------------------------
    {recommendations}
    
    Veuillez consulter le Dashboard pour plus de détails : http://localhost:8501
    
    -- 
    LogiSphere AI Notifier
    """

    if not SMTP_USER or not SMTP_PASS:
        # Fallback for demo: Write to a mock alert log
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports")
        os.makedirs(log_dir, exist_ok=True)
        alert_log = os.path.join(log_dir, "SENT_ALERTS_MOCK.txt")
        
        with open(alert_log, "a") as f:
            f.write(f"\n--- NEW ALERT ---\nSubject: {subject}\n{body}\n-----------------\n")
        
        print(f"📡 Mock Alert Generated (No SMTP credentials found) -> {alert_log}")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER # Sending to self as default
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Alert Email Sent Successfully!")
    except Exception as e:
        print(f"❌ Failed to send alert email: {str(e)}")
