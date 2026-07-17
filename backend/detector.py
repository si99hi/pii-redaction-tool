import re
import random
from faker import Faker

analyzer = None
nlp = None
fake = Faker()


def initialize_detector():
    """Init detector."""
    global analyzer, nlp

    if analyzer is None:
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            # Configure Presidio to use en_core_web_sm instead of en_core_web_lg to fit within 512MB RAM
            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": [
                    {
                        "lang_code": "en",
                        "model_name": "en_core_web_sm"
                    }
                ]
            }
            provider = NlpEngineProvider(nlp_configuration=nlp_config)
            nlp_engine = provider.create_engine()
            analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        except ImportError as e:
            raise RuntimeError(
                "Presidio Analyzer is required."
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
    """Filter likely PII."""
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
    """Generate fake phone."""
    clean_original = original.strip()
    if clean_original.startswith("+91"):
        random_digits = "".join(str(random.randint(0, 9)) for _ in range(10))
        return f"+91 {random_digits}"
    return fake.phone_number()

def generate_fake_address(original: str) -> str:
    """Generate fake address."""
    if any(c.isdigit() for c in original):
        return fake.address().replace("\n", ", ")
    return fake.city()

def generate_fake_date(original: str) -> str:
    """Generate fake DOB."""
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
    """Add non-overlapping detection."""
    for d in detections:
        if start < d["end"] and end > d["start"]:
            return False
    detections.append({
        "start": start,
        "end": end,
        "entity_type": entity_type
    })
    return True


# Define the set of whitelisted terms (lowercase, stripped of punctuation)
WHITELISTED_TERMS = {
    "company", "prospectus", "registrar of companies", "book building process", 
    "offer", "equity shares", "board of india", "board of directors", "board",
    "sebi", "securities and exchange board of india", "registrar", "roc",
    "companies act", "promoter", "promoters", "draft red herring prospectus",
    "red herring prospectus", "drhp", "rhp", "government of india", "government",
    "equity share", "shares", "share", "public issue", "issue", "book running lead manager",
    "book running lead managers", "brlm", "brlms", "selling shareholder", "selling shareholders",
    "memorandum of association", "moa", "articles of association", "aoa",
    "stock exchange", "designated stock exchange", "national stock exchange of india limited",
    "nse", "bse limited", "bse", "state bank of india", "sbi", "reserve bank of india", "rbi",
    "registrar of companies, maharashtra",
    "registrar of companies, maharashtra at pune",
    "registrar of companies, maharashtra at mumbai",
    "registrar of companies, maharashtra at bombay",
    "registrar of companies, central processing centre",
    "regional director",
    
    # Newly expanded terms (from user review and legal document analysis)
    "abridged prospectus", "letter of offer", "offer for sale", "fresh issue",
    "director", "directors", "our board of directors", "board of directors",
    "company secretary", "compliance officer", "statutory auditor", "statutory auditors",
    "auditor", "auditors", "promoter group", "promoters group", "our promoter", "our promoters",
    "group company", "group companies", "subsidiary", "subsidiaries", "associate", "associates",
    "joint venture", "joint ventures", "key managerial personnel", "kmp", "kmps",
    "senior management", "eligible employee", "eligible employees", "mutual fund", "mutual funds",
    "alternative investment fund", "alternative investment funds", "aif", "aifs",
    "foreign portfolio investor", "foreign portfolio investors", "fpi", "fpis",
    "qualified institutional buyer", "qualified institutional buyers", "qib", "qibs",
    "non-institutional bidder", "non-institutional bidders", "nib", "nibs",
    "retail individual bidder", "retail individual bidders", "rib", "ribs",
    "bid", "bids", "bidding", "bidder", "bidders", "allotment", "allotted", "allottee", "allottees",
    "application form", "asba", "self certified syndicate bank", "self certified syndicate banks",
    "scsb", "scsbs", "syndicate member", "syndicate members", "depository", "depositories",
    "nsdl", "cdsl", "national securities depository limited", "central depository services india limited",
    "registrar to the offer", "registrar to the issue", "working day", "working days",
    "fema", "foreign exchange management act", "scra", "scrr", "sebi act", "companies act, 1956",
    "companies act, 2013", "income tax act", "it act", "ind as", "indian gaap", "ifrs",
    "central processing centre", "cpc", "official liquidator", "high court", "supreme court",
    "nclt", "national company law tribunal", "corporate debt restructuring", "cdr",
    "offer price", "floor price", "cap price", "india", "indian", "regulation", "rule", "section",
    "certificate", "corporate identity number", "cin", "isin", "pan", "gstin", "united states",
    "us", "usa", "united kingdom", "uk", "singapore", "japan", "germany", "france", "canada",
    "australia", "china", "europe", "asia", "maharashtra", "pune", "mumbai", "bombay", "delhi",
    "bengaluru", "bangalore", "hyderabad", "chennai", "kolkata", "gujarat", "karnataka", "haryana",
    "rajasthan", "material contract", "due diligence", "regulatory action", "pre-issue", "post-issue"
}

DOB_KEYWORDS_REGEX = re.compile(r'\b(?:birth|born|dob|d\.o\.b)\b', re.IGNORECASE)

# Structured Indian corporate and financial identifiers to protect from redaction
STRUCTURED_ID_PATTERNS = [
    re.compile(r'\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b', re.IGNORECASE), # CIN (Corporate Identification Number)
    re.compile(r'\b[A-Z]{2}[A-Z0-9]{9}\d\b', re.IGNORECASE),              # ISIN (Securities Identifier)
    re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b', re.IGNORECASE),                 # PAN (Permanent Account Number)
    re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]{3}\b', re.IGNORECASE), # GSTIN
    re.compile(r'\bIN[A-Z0-9]\d{9}\b', re.IGNORECASE),                    # SEBI Intermediary Registration Number
    re.compile(r'\bIN-[A-Z0-9\-]{5,15}\b', re.IGNORECASE),                # SEBI Registration formats
]

def is_whitelisted(text: str) -> bool:
    import string
    chars_to_strip = string.punctuation + '“”‘’"\'–—•'
    clean_text = text.strip(chars_to_strip + " \n\r\t").lower()
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text in WHITELISTED_TERMS

COMMON_LEGAL_FINANCIAL_WORDS = {
    "offer", "issue", "shares", "equity", "price", "process", "procedure",
    "board", "committee", "investor", "promoter", "regulation", "section",
    "rule", "act", "certificate", "registration", "prospectus", "capital",
    "risk", "listing", "draft", "herring", "red", "rhp", "drhp", "aoa", "moa",
    "document", "application", "bid", "bidding", "allotment", "allotted",
    "allottee", "annexure", "schedule", "table", "clause", "index", "period",
    "date", "dated", "amount", "rupees", "rs", "crore", "crores", "lakh", "lakhs",
    "corporate", "office", "officer", "secretary", "compliance", "auditor", "auditors",
    "authority", "authorities", "ministry", "department", "government", "state", "national",
    "stock", "exchange", "exchanges", "depository", "depositories", "bank", "banks",
    "banking", "financial", "securities", "mutual", "fund", "funds", "investors",
    "shareholder", "shareholders", "director", "directors", "employee", "employees",
    "manager", "managers", "management", "personnel", "promoters", "partner", "partners",
    "member", "members", "meeting", "meetings", "resolution", "resolutions", "registrar",
    "registrars", "company", "companies", "counsel", "advisor", "advisors", "advisory",
    "underwriter", "underwriters", "underwriting", "syndicate", "sponsor", "sponsors",
    "clearing", "corporation", "corporations", "index", "indices", "period", "periods",
    "time", "times", "day", "days", "week", "weeks", "month", "months", "year", "years",
    "pre-issue", "post-issue", "bonus", "split"
}

FOLLOWED_BY_TRIGGERS = {
    "issue", "issues", "price", "prices", "shares", "share", "process", "procedure",
    "procedures", "regulation", "regulations", "period", "periods", "office", "offices",
    "meeting", "meetings", "resolution", "resolutions", "act", "acts", "rule", "rules",
    "section", "sections", "portion", "portions", "category", "categories", "bid", "bids",
    "bidding", "offer", "offers", "offering", "offerings", "prospectus"
}

def contains_common_legal_word(text: str) -> bool:
    words = re.findall(r'\b\w+\b', text.lower())
    for w in words:
        if w in COMMON_LEGAL_FINANCIAL_WORDS:
            return True
    return False

def is_followed_by_legal_trigger(full_text: str, entity_end: int) -> bool:
    after_text = full_text[entity_end:entity_end + 30].strip()
    if not after_text:
        return False
    first_word_match = re.match(r'^([a-zA-Z0-9\-]+)', after_text)
    if first_word_match:
        first_word = first_word_match.group(1).lower()
        if first_word in FOLLOWED_BY_TRIGGERS:
            return True
    return False

def should_skip_entity(full_text: str, start: int, end: int, entity_type: str) -> bool:
    if entity_type not in ["COMPANY", "PERSON", "ADDRESS"]:
        return False
    val = full_text[start:end]
    if is_whitelisted(val):
        return True
    if contains_common_legal_word(val):
        return True
    if is_followed_by_legal_trigger(full_text, end):
        return True
    return False

def is_dob_like_date(text: str, start: int, end: int) -> bool:
    ctx_start = max(0, start - 50)
    ctx_end = min(len(text), end + 15)
    context = text[ctx_start:ctx_end].lower()
    return bool(DOB_KEYWORDS_REGEX.search(context))

def detect_pii(text: str) -> list:
    """Scan PII."""
    if not text or not text.strip():
        return []

    protected_spans = []
    for pattern in STRUCTURED_ID_PATTERNS:
        for match in pattern.finditer(text):
            protected_spans.append(match.span())

    def is_protected(start: int, end: int) -> bool:
        for p_start, p_end in protected_spans:
            if start < p_end and end > p_start:
                return True
        return False

    detections = []

    if likely_pii_text(text):
        presidio_entities = [
            "EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER", 
            "LOCATION", "US_SSN", "CREDIT_CARD", 
            "DATE_TIME", "IP_ADDRESS"
        ]
        results = analyzer.analyze(
            text=text,
            entities=presidio_entities,
            language="en"
        )

        for r in results:
            if is_protected(r.start, r.end):
                continue

            et = r.entity_type
            if et == "LOCATION":
                et = "ADDRESS"
            elif et == "US_SSN":
                et = "SSN"
            elif et == "DATE_TIME":
                et = "DATE"
                
            # For DATE, only keep if it is DOB-like
            if et == "DATE" and not is_dob_like_date(text, r.start, r.end):
                continue
                
            if should_skip_entity(text, r.start, r.end, et):
                continue

            detections.append({
                "start": r.start,
                "end": r.end,
                "entity_type": et
            })

        if nlp is not None:
            spacy_doc = nlp(text)
            for ent in spacy_doc.ents:
                if ent.label_ == "ORG":
                    if is_protected(ent.start_char, ent.end_char):
                        continue
                    if should_skip_entity(text, ent.start_char, ent.end_char, "COMPANY"):
                        continue
                    add_detection_if_no_overlap(detections, ent.start_char, ent.end_char, "COMPANY")

    for match in COMPANY_REGEX.finditer(text):
        start, end = match.span()
        if is_protected(start, end):
            continue
        if should_skip_entity(text, start, end, "COMPANY"):
            continue
        add_detection_if_no_overlap(detections, start, end, "COMPANY")

    for match in ADDRESS_REGEX.finditer(text):
        start, end = match.span()
        if is_protected(start, end):
            continue
        if should_skip_entity(text, start, end, "ADDRESS"):
            continue
        add_detection_if_no_overlap(detections, start, end, "ADDRESS")

    for match in SSN_REGEX.finditer(text):
        start, end = match.span()
        if is_protected(start, end):
            continue
        if should_skip_entity(text, start, end, "SSN"):
            continue
        add_detection_if_no_overlap(detections, start, end, "SSN")

    for match in CC_REGEX.finditer(text):
        start, end = match.span()
        if is_protected(start, end):
            continue
        if should_skip_entity(text, start, end, "CREDIT_CARD"):
            continue
        add_detection_if_no_overlap(detections, start, end, "CREDIT_CARD")

    for match in IP_REGEX.finditer(text):
        start, end = match.span()
        if is_protected(start, end):
            continue
        if should_skip_entity(text, start, end, "IP_ADDRESS"):
            continue
        add_detection_if_no_overlap(detections, start, end, "IP_ADDRESS")

    for match in DATE_REGEX.finditer(text):
        start, end = match.span()
        if is_protected(start, end):
            continue
        if is_dob_like_date(text, start, end):
            if should_skip_entity(text, start, end, "DATE"):
                continue
            add_detection_if_no_overlap(detections, start, end, "DATE")

    for match in PHONE_REGEX.finditer(text):
        start, end = match.span()
        if is_protected(start, end):
            continue
        if should_skip_entity(text, start, end, "PHONE_NUMBER"):
            continue
        add_detection_if_no_overlap(detections, start, end, "PHONE_NUMBER")

    return detections


def scan_and_build_mapping(texts: list, mapping: dict = None, counts: dict = None) -> tuple:
    """Build PII mapping."""
    initialize_detector()

    if mapping is None:
        mapping = {}
    if counts is None:
        counts = {}

    for text in texts:
        if not text.strip():
            continue

        detections = detect_pii(text)

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
