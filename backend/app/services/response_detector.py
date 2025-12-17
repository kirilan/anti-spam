"""
Response Detector Service
Classifies broker email responses based on keyword matching
"""
import re
from typing import Tuple, Optional
from app.models.broker_response import ResponseType


class ResponseDetector:
    """Detects and classifies broker responses to deletion requests"""

    # Keyword patterns for each response type
    CONFIRMATION_KEYWORDS = [
        'deleted', 'removed', 'erasure complete', 'data erased',
        'successfully deleted', 'removed from our database',
        'removed from our system', 'no longer in our records',
        'deletion complete', 'account closed', 'account deleted',
        'unsubscribed', 'removed from our list', 'opt-out confirmed',
        'request completed', 'successfully processed your request to delete'
    ]

    REJECTION_KEYWORDS = [
        'unable to delete', 'cannot delete', 'denied', 'rejected',
        'no record found', 'no records found', 'could not find',
        'we do not have', 'not in our system', 'not in our database',
        'unable to locate', 'cannot verify', 'insufficient information',
        'cannot process', 'unable to fulfill', 'request denied'
    ]

    ACKNOWLEDGMENT_KEYWORDS = [
        'acknowledged', 'acknowledge', 'received your request', 'processing your request',
        'reviewing your request', 'working on your request',
        'will process', 'will review', 'in progress',
        'under review', 'being processed', 'ticket created',
        'case number', 'reference number', 'request number',
        'acknowledge receipt', 'received and will', 'thank you for contacting'
    ]

    REQUEST_INFO_KEYWORDS = [
        'need more information', 'need additional information',
        'verify your identity', 'confirm your identity',
        'additional details', 'provide more details',
        'please provide', 'require verification',
        'identity verification', 'verify that you are',
        'confirm that you', 'need to verify', 'unable to verify'
    ]

    def __init__(self):
        # Compile regex patterns for efficiency
        self.confirmation_pattern = self._compile_pattern(self.CONFIRMATION_KEYWORDS)
        self.rejection_pattern = self._compile_pattern(self.REJECTION_KEYWORDS)
        self.acknowledgment_pattern = self._compile_pattern(self.ACKNOWLEDGMENT_KEYWORDS)
        self.request_info_pattern = self._compile_pattern(self.REQUEST_INFO_KEYWORDS)

    def _compile_pattern(self, keywords: list) -> re.Pattern:
        """Compile a list of keywords into a single regex pattern"""
        # Escape special regex characters and join with OR
        pattern = '|'.join(re.escape(kw) for kw in keywords)
        return re.compile(pattern, re.IGNORECASE)

    def detect_response_type(
        self,
        subject: Optional[str],
        body: Optional[str]
    ) -> Tuple[ResponseType, float]:
        """
        Detect the type of response based on subject and body content

        Args:
            subject: Email subject line
            body: Email body text

        Returns:
            Tuple of (ResponseType, confidence_score)
            confidence_score ranges from 0.0 to 1.0
        """
        # Combine subject and body for analysis
        text = ' '.join(filter(None, [subject or '', body or ''])).lower()

        if not text:
            return (ResponseType.UNKNOWN, 0.0)

        # Count matches for each response type
        matches = {
            ResponseType.CONFIRMATION: len(self.confirmation_pattern.findall(text)),
            ResponseType.REJECTION: len(self.rejection_pattern.findall(text)),
            ResponseType.ACKNOWLEDGMENT: len(self.acknowledgment_pattern.findall(text)),
            ResponseType.REQUEST_INFO: len(self.request_info_pattern.findall(text))
        }

        # Find the type with the most matches
        max_matches = max(matches.values())

        if max_matches == 0:
            return (ResponseType.UNKNOWN, 0.0)

        # Get the response type with the most matches
        detected_type = max(matches.items(), key=lambda x: x[1])[0]

        # Calculate confidence score
        # Base confidence on number of matches and text length
        text_words = len(text.split())
        if text_words == 0:
            confidence = 0.0
        else:
            # More matches relative to text length = higher confidence
            match_ratio = max_matches / max(text_words / 10, 1)
            confidence = min(match_ratio * 0.3 + 0.4, 1.0)  # Scale to 0.4-1.0 range

        # Boost confidence if matches found in subject (more reliable)
        if subject and self._has_keyword_match(detected_type, subject.lower()):
            confidence = min(confidence + 0.15, 1.0)

        return (detected_type, round(confidence, 2))

    def _has_keyword_match(self, response_type: ResponseType, text: str) -> bool:
        """Check if text contains keywords for the given response type"""
        pattern_map = {
            ResponseType.CONFIRMATION: self.confirmation_pattern,
            ResponseType.REJECTION: self.rejection_pattern,
            ResponseType.ACKNOWLEDGMENT: self.acknowledgment_pattern,
            ResponseType.REQUEST_INFO: self.request_info_pattern
        }

        pattern = pattern_map.get(response_type)
        if not pattern:
            return False

        return bool(pattern.search(text))

    def extract_case_number(self, text: str) -> Optional[str]:
        """
        Extract case/ticket/reference number from text

        Args:
            text: Email subject or body

        Returns:
            Case number if found, None otherwise
        """
        if not text:
            return None

        # Common patterns for case numbers
        patterns = [
            r'case\s*#?\s*([A-Z0-9-]+)',
            r'ticket\s*#?\s*([A-Z0-9-]+)',
            r'reference\s*#?\s*([A-Z0-9-]+)',
            r'request\s*#?\s*([A-Z0-9-]+)',
            r'#\s*([A-Z0-9-]{6,})'  # Generic #XXXXX format
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
