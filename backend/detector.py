import re
import random
from faker import Faker

analyzer = None
nlp = None
fake = Faker()


def initialize_detector():
    """Initialize the heavy PII detection backends only when needed."""
    global analyzer, nlp

    if analyzer is None:
        try:
            from presidio_analyzer import AnalyzerEngine
            analyzer = AnalyzerEngine()
        except ImportError as e:
            raise RuntimeError(
                "Presidio Analyzer is required for detection. Install it with `pip install presidio-analyzer`."
            ) from e

    if nlp is None:
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            try:
                import spacy
                nlp = spacy.blank("en")
            except ImportError:
                nlp = None

PHONE_REGEX = re.compile(r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b')

COMPANY_REGEX = re.compile(
    r'\b[A-Z][a-zA-Z0-9&\s\-\.]{1,40}?\s(?:Ltd|Limited|Pvt\s+Ltd|LLP|Inc|LLC|Corp|Corporation)\b',
    re.IGNORECASE
)

PII_KEYWORDS = re.compile(
    r'\b(?:Inc|LLP|LLC|Ltd|Limited|Pvt\s+Ltd|Corp|Corporation|Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Highway|Hwy|Loop|Plaza|Plz|Mr|Mrs|Ms|Dr|Prof|CEO|Founder|Director|President)\b',
    re.IGNORECASE
)

CAPITALIZED_WORDS_REGEX = re.compile(r"\b[A-Z][a-z]+\b")


def likely_pii_text(text: str) -> bool:
    """Heuristic filter to skip non-PII text before the expensive analyzer step."""
    if not text or not text.strip():
        return False

    if "@" in text:
        return True
    if PHONE_REGEX.search(text):
        return True
    if COMPANY_REGEX.search(text):
        return True
    if SSN_REGEX.search(text):
        return True
    if CC_REGEX.search(text):
        return True
    if IP_REGEX.search(text):
        return True
    if DATE_REGEX.search(text):
        return True
    if ADDRESS_REGEX.search(text):
        return True
    if PII_KEYWORDS.search(text):
        return True

    capitalized_words = CAPITALIZED_WORDS_REGEX.findall(text)
    if len(capitalized_words) >= 3 and len(text.split()) <= 12:
        return True

    return False

ADDRESS_REGEX = re.compile(
    r'\b\d{1,5}\s+(?:[A-Z][a-zA-Z0-9\s\.\,\-\#]{2,40}?)\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Highway|Hwy|Loop|Plaza|Plz)\b',
    re.IGNORECASE
)

SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

CC_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{13,19}\b')

IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

DATE_REGEX = re.compile(
    r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b', 
    re.IGNORECASE
)


def generate_fake_phone(original: str) -> str:
    """
    Generates a fake phone number. Preserves +91 prefix for Indian numbers.
    """
    clean_original = original.strip()
    if clean_original.startswith("+91"):
        random_digits = "".join(str(random.randint(0, 9)) for _ in range(10))
        return f"+91 {random_digits}"
    return fake.phone_number()

def generate_fake_address(original: str) -> str:
    """
    Generates a fake address. Uses fake.city() for single locations/cities
    and fake.address() for full street addresses.
    """
    if any(c.isdigit() for c in original):
        # Format address on a single line
        return fake.address().replace("\n", ", ")
    return fake.city()

def generate_fake_date(original: str) -> str:
    """
    Generates a fake date of birth while preserving the format (slashes, hyphens, textual month).
    """
    fake_dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
    clean_original = original.strip()
    
 
    if re.match(r'^\d{4}-\d{2}-\d{2}$', clean_original):
        return fake_dob.strftime('%Y-%m-%d')
    elif re.match(r'^\d{2}/\d{2}/\d{4}$', clean_original):
        return fake_dob.strftime('%d/%m/%Y')
    elif re.match(r'^\d{2}-\d{2}-\d{4}$', clean_original):
        return fake_dob.strftime('%d-%m-%Y')
    elif any(c.isalpha() for c in clean_original):
        return fake_dob.strftime('%B %d, %Y')
    else:
        return fake_dob.strftime('%Y-%m-%d')

def add_detection_if_no_overlap(detections: list, start: int, end: int, entity_type: str) -> bool:
    """
    Checks if a span overlaps with any existing detections. If not, adds it.
    """
    for d in detections:
        if start < d["end"] and end > d["start"]:
            return False
    detections.append({
        "start": start,
        "end": end,
        "entity_type": entity_type
    })
    return True


def scan_and_build_mapping(texts: list, mapping: dict = None, counts: dict = None) -> tuple:
    """
    Scans a list of text strings for PII.
    Generates a consistent mapping dictionary (original -> fake) and counts detections.
    """
    initialize_detector()

    if mapping is None:
        mapping = {}
    if counts is None:
        counts = {}

    presidio_entities = [
        "EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER", 
        "LOCATION", "US_SSN", "CREDIT_CARD", 
        "DATE_TIME", "IP_ADDRESS"
    ]

    for text in texts:
        if not text.strip():
            continue

        detections = []

        if likely_pii_text(text):
            results = analyzer.analyze(
                text=text,
                entities=presidio_entities,
                language="en"
            )

            for r in results:
                et = r.entity_type
                if et == "LOCATION":
                    et = "ADDRESS"
                elif et == "US_SSN":
                    et = "SSN"
                elif et == "DATE_TIME":
                    et = "DATE"
                    
                detections.append({
                    "start": r.start,
                    "end": r.end,
                    "entity_type": et
                })

            if nlp is not None:
                spacy_doc = nlp(text)
                for ent in spacy_doc.ents:
                    if ent.label_ == "ORG":
                        add_detection_if_no_overlap(detections, ent.start_char, ent.end_char, "COMPANY")

        for match in COMPANY_REGEX.finditer(text):
            start, end = match.span()
            add_detection_if_no_overlap(detections, start, end, "COMPANY")

        for match in ADDRESS_REGEX.finditer(text):
            start, end = match.span()
            add_detection_if_no_overlap(detections, start, end, "ADDRESS")

        for match in SSN_REGEX.finditer(text):
            start, end = match.span()
            add_detection_if_no_overlap(detections, start, end, "SSN")

        for match in CC_REGEX.finditer(text):
            start, end = match.span()
            add_detection_if_no_overlap(detections, start, end, "CREDIT_CARD")

        for match in IP_REGEX.finditer(text):
            start, end = match.span()
            add_detection_if_no_overlap(detections, start, end, "IP_ADDRESS")

        for match in DATE_REGEX.finditer(text):
            start, end = match.span()
            add_detection_if_no_overlap(detections, start, end, "DATE")

        for match in PHONE_REGEX.finditer(text):
            start, end = match.span()
            add_detection_if_no_overlap(detections, start, end, "PHONE_NUMBER")

        for d in detections:
            start = d["start"]
            end = d["end"]
            entity_type = d["entity_type"]
            original = text[start:end]

            counts[entity_type] = counts.get(entity_type, 0) + 1

            if original not in mapping:
                if entity_type == "EMAIL_ADDRESS":
                    mapping[original] = fake.email()
                elif entity_type == "PERSON":
                    mapping[original] = fake.name()
                elif entity_type == "PHONE_NUMBER":
                    mapping[original] = generate_fake_phone(original)
                elif entity_type == "COMPANY":
                    mapping[original] = fake.company()
                elif entity_type == "ADDRESS":
                    mapping[original] = generate_fake_address(original)
                elif entity_type == "SSN":
                    mapping[original] = fake.ssn()
                elif entity_type == "CREDIT_CARD":
                    mapping[original] = fake.credit_card_number()
                elif entity_type == "IP_ADDRESS":
                    mapping[original] = fake.ipv4()
                elif entity_type == "DATE":
                    mapping[original] = generate_fake_date(original)

    sorted_mapping = dict(sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True))

    return sorted_mapping, counts
