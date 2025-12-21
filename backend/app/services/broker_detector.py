import re

from bs4 import BeautifulSoup

from app.models.data_broker import DataBroker


class BrokerDetector:
    # Keywords that suggest data broker communication
    PRIVACY_KEYWORDS = [
        "opt out",
        "opt-out",
        "remove your information",
        "data privacy",
        "personal information",
        "public records",
        "background check",
        "people search",
        "data broker",
        "marketing list",
        "unsubscribe",
        "ccpa",
        "gdpr",
        "privacy rights",
        "data deletion",
    ]

    def detect_broker(
        self,
        sender_email: str,
        sender_domain: str,
        subject: str,
        body_html: str,
        body_text: str,
        all_brokers: list[DataBroker],
    ) -> tuple[DataBroker | None, float, str]:
        """
        Detect if email is from a data broker

        Returns:
            (broker, confidence_score, notes)
        """
        # First check if sender domain matches a known broker
        for broker in all_brokers:
            for domain in broker.domains:
                if domain in sender_domain:
                    return (broker, 1.0, f"Direct domain match: {domain}")

        # Parse email body for keywords
        text_to_analyze = f"{subject or ''} {body_text or ''}"

        # Remove HTML if present
        if body_html:
            soup = BeautifulSoup(body_html, "html.parser")
            text_to_analyze += " " + soup.get_text()

        text_to_analyze = text_to_analyze.lower()

        # Count privacy keyword matches
        keyword_matches = []
        for keyword in self.PRIVACY_KEYWORDS:
            if keyword in text_to_analyze:
                keyword_matches.append(keyword)

        # Calculate confidence score
        if len(keyword_matches) >= 3:
            confidence = 0.7
        elif len(keyword_matches) >= 2:
            confidence = 0.5
        elif len(keyword_matches) >= 1:
            confidence = 0.3
        else:
            confidence = 0.0

        if confidence > 0:
            notes = f"Keyword matches: {', '.join(keyword_matches[:5])}"
            return (None, confidence, notes)

        return (None, 0.0, "No broker indicators found")

    def extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email address"""
        if "@" in email:
            return email.split("@")[1].lower()
        return email.lower()

    def get_body_preview(self, body_html: str, body_text: str, max_length: int = 200) -> str:
        """Get a preview of email body"""
        if body_text:
            preview = body_text[:max_length]
        elif body_html:
            soup = BeautifulSoup(body_html, "html.parser")
            preview = soup.get_text()[:max_length]
        else:
            preview = ""

        # Clean up preview
        preview = re.sub(r"\s+", " ", preview).strip()

        if len(preview) == max_length:
            preview += "..."

        return preview
