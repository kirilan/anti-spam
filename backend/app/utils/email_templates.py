import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Framework to template file mapping
FRAMEWORK_TEMPLATES = {
    "GDPR": "deletion_request_gdpr.txt",
    "CCPA": "deletion_request_ccpa.txt",
    "GDPR/CCPA": "deletion_request_combined.txt",
}

# Deadline days by framework
FRAMEWORK_DEADLINES = {
    "GDPR": 30,
    "CCPA": 45,
    "GDPR/CCPA": 30,
}


class EmailTemplates:
    _template_cache: dict[str, str] = {}

    @classmethod
    def _load_template(cls, template_name: str) -> str | None:
        """Load a template file, with caching"""
        if template_name in cls._template_cache:
            return cls._template_cache[template_name]

        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            logger.warning(f"Template not found: {template_path}")
            return None

        try:
            content = template_path.read_text(encoding="utf-8")
            cls._template_cache[template_name] = content
            return content
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            return None

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the template cache (useful for testing or hot-reload)"""
        cls._template_cache.clear()

    @staticmethod
    def _render_template(template: str, context: dict) -> str:
        """Simple template rendering using {{ variable }} syntax"""
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{{ {key} }}}}", str(value))
        return result

    @classmethod
    def generate_deletion_request_email(
        cls, user_email: str, broker_name: str, framework: str = "GDPR/CCPA"
    ) -> tuple[str, str]:
        """
        Generate deletion request email from template

        Args:
            user_email: User's email address
            broker_name: Name of the data broker
            framework: Legal framework (GDPR, CCPA, or GDPR/CCPA)

        Returns:
            (subject, body)
        """
        # Normalize framework
        framework = framework.upper().strip()
        if framework not in FRAMEWORK_TEMPLATES:
            logger.warning(f"Unknown framework {framework}, defaulting to GDPR/CCPA")
            framework = "GDPR/CCPA"

        subject = f"Data Deletion Request under {framework}"

        # Calculate deadline
        deadline_days = FRAMEWORK_DEADLINES.get(framework, 30)
        deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%B %d, %Y")

        # Load and render template
        template_file = FRAMEWORK_TEMPLATES[framework]
        template = cls._load_template(template_file)

        if template:
            context = {
                "user_email": user_email,
                "broker_name": broker_name,
                "deadline": deadline,
            }
            body = cls._render_template(template, context)
        else:
            # Fallback to inline template if file not found
            logger.warning(f"Using fallback template for {framework}")
            body = cls._generate_fallback_body(user_email, broker_name, framework, deadline)

        return subject, body

    @staticmethod
    def _generate_fallback_body(
        user_email: str, broker_name: str, framework: str, deadline: str
    ) -> str:
        """Generate fallback email body if template file is unavailable"""
        if "GDPR" in framework:
            legal_ref = "Under Article 17 of the GDPR, I have the right to request erasure of my personal data."
        else:
            legal_ref = (
                "Under the CCPA, I have the right to request deletion of my personal information."
            )

        return f"""Dear {broker_name} Privacy Team,

I am formally requesting the complete deletion of all my personal data from your systems.

{legal_ref}

Please delete all information associated with: {user_email}

Please confirm receipt within 5 business days and complete the deletion by {deadline}.

Sincerely,
{user_email}
"""

    @classmethod
    def generate_gdpr_request(cls, user_email: str, broker_name: str) -> tuple[str, str]:
        """Generate GDPR-specific deletion request"""
        return cls.generate_deletion_request_email(user_email, broker_name, framework="GDPR")

    @classmethod
    def generate_ccpa_request(cls, user_email: str, broker_name: str) -> tuple[str, str]:
        """Generate CCPA-specific deletion request"""
        return cls.generate_deletion_request_email(user_email, broker_name, framework="CCPA")
