"""
scrapers.py — Internship & Scholarship recommendation engine
============================================================
Targets:
  - Rekrute.com   (Moroccan internship portal, BS4-friendly)
  - Emploi.ma     (Moroccan job board, BS4-friendly)
  - Static DB     (Curated scholarships: Campus France, DAAD, Erasmus, Fulbright)

NOT targeted (blocked / JS-rendered):
  - LinkedIn  → ToS + Cloudflare, always returns 999
  - Indeed    → dynamic JS, BeautifulSoup sees an empty shell

Usage:
    from scrapers import recommend_opportunities
    results = recommend_opportunities(predicted_branch="IADATA", gpa=14.5)
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────────────

# Rotate User-Agents to reduce chance of being rate-limited
_UA_POOL = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.3 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
]

# Keywords used to build search queries per branch
BRANCH_KEYWORDS: dict[str, list[str]] = {
    "IADATA": [
        "data science", "machine learning", "intelligence artificielle",
        "data analyst", "deep learning", "NLP", "computer vision",
    ],
    "DSI": [
        "développeur web", "full stack", "développeur logiciel",
        "développeur mobile", "DevOps", "software engineer", "backend",
    ],
    "CIR": [
        "cybersécurité", "réseaux informatiques", "administrateur système",
        "sécurité informatique", "infrastructure IT", "ethical hacking",
    ],
}

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Opportunity:
    title:       str
    company:     str
    location:    str
    url:         str
    source:      str
    kind:        str          # "stage" | "scholarship"
    description: str  = ""
    deadline:    str  = "N/A"
    tags:        list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "Titre":       self.title,
            "Entreprise":  self.company,
            "Lieu":        self.location,
            "Type":        self.kind,
            "Source":      self.source,
            "Deadline":    self.deadline,
            "Description": self.description,
            "URL":         self.url,
            "Tags":        ", ".join(self.tags),
        }

# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent":      random.choice(_UA_POOL),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
        "Referer":         "https://www.google.com/",
    })
    return s


def _get(session: requests.Session, url: str, timeout: int = 12) -> Optional[requests.Response]:
    """GET with error handling. Returns None on any failure."""
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        time.sleep(random.uniform(1.2, 2.4))   # polite delay between requests
        return resp
    except requests.RequestException:
        return None

# ── Scraper: Rekrute.com ──────────────────────────────────────────────────────

def _scrape_rekrute(keywords: list[str], max_results: int = 5) -> list[Opportunity]:
    """
    Scrapes Rekrute.com for internship listings matching the given keywords.
    URL pattern: https://www.rekrute.com/offres.html?s=3&p=1&o=1&q=QUERY
      s=3  → filter: stage (internship)
      o=1  → sort: latest first
    """
    query   = "+".join(keywords[:2])          # use top 2 keywords
    url     = f"https://www.rekrute.com/offres.html?s=3&p=1&o=1&q={query}"
    session = _session()
    resp    = _get(session, url)

    if resp is None:
        return []

    soup    = BeautifulSoup(resp.text, "lxml")
    results = []

    # Each job posting is inside a <li class="post-id ...">
    for post in soup.select("li.post-id")[:max_results]:
        try:
            title_tag   = post.select_one("a.titreJob") or post.select_one("h2 a")
            company_tag = post.select_one("a.nomEntreprise") or post.select_one(".company")
            city_tag    = post.select_one(".ville") or post.select_one(".location")

            if not title_tag:
                continue

            href = title_tag.get("href", "")
            full_url = ("https://www.rekrute.com" + href) if href.startswith("/") else href

            results.append(Opportunity(
                title    = title_tag.get_text(strip=True),
                company  = company_tag.get_text(strip=True) if company_tag else "N/A",
                location = city_tag.get_text(strip=True)    if city_tag    else "Maroc",
                url      = full_url,
                source   = "Rekrute.ma",
                kind     = "stage",
                tags     = keywords[:3],
            ))
        except Exception:
            continue

    return results

# ── Scraper: Emploi.ma ────────────────────────────────────────────────────────

def _scrape_emploima(keywords: list[str], max_results: int = 5) -> list[Opportunity]:
    """
    Scrapes Emploi.ma for internship listings.
    URL pattern: https://www.emploi.ma/recherche-jobs-maroc/KEYWORD.html
    """
    keyword = "-".join(keywords[0].split())     # first keyword, slug format
    url     = f"https://www.emploi.ma/recherche-jobs-maroc/{keyword}.html"
    session = _session()
    resp    = _get(session, url)

    if resp is None:
        return []

    soup    = BeautifulSoup(resp.text, "lxml")
    results = []

    # Emploi.ma wraps each offer in <div class="card offer-card ...">
    for card in soup.select("div.card.offer-card, article.job-list-item")[:max_results]:
        try:
            title_tag   = card.select_one("h3 a, h2 a, a.job-title")
            company_tag = card.select_one(".company-name, .firm-name, span.company")
            city_tag    = card.select_one(".job-location, .location, span.city")

            if not title_tag:
                continue

            href     = title_tag.get("href", "")
            full_url = href if href.startswith("http") else "https://www.emploi.ma" + href

            results.append(Opportunity(
                title    = title_tag.get_text(strip=True),
                company  = company_tag.get_text(strip=True) if company_tag else "N/A",
                location = city_tag.get_text(strip=True)    if city_tag    else "Maroc",
                url      = full_url,
                source   = "Emploi.ma",
                kind     = "stage",
                tags     = keywords[:3],
            ))
        except Exception:
            continue

    return results

# ── Static scholarship database ───────────────────────────────────────────────
# Scrapers break when scholarship sites redesign. A curated list is more
# reliable and always returns results — we just filter by branch relevance.

_SCHOLARSHIPS: list[dict] = [
    # ── Campus France (France) ────────────────────────────────────────────────
    {
        "title":    "Bourse d'Excellence Eiffel — Campus France",
        "company":  "Campus France / Gouvernement Français",
        "location": "France",
        "url":      "https://www.campusfrance.org/fr/eiffel",
        "deadline": "Janvier (chaque année)",
        "desc":     "Bourse pour masters et doctorats en France. Couvre frais de vie, transport et assurance.",
        "tags":     ["IADATA", "DSI", "CIR"],
        "gpa_min":  14.0,
    },
    {
        "title":    "Bourses du Gouvernement Français (BGF)",
        "company":  "Institut Français du Maroc",
        "location": "France",
        "url":      "https://www.institutfrancais-maroc.com/bourses",
        "deadline": "Avril (chaque année)",
        "desc":     "Bourses pour étudiants marocains souhaitant poursuivre des études en France.",
        "tags":     ["IADATA", "DSI", "CIR"],
        "gpa_min":  13.0,
    },
    # ── DAAD (Allemagne) ──────────────────────────────────────────────────────
    {
        "title":    "DAAD Scholarship — Master's in Germany",
        "company":  "DAAD (Service Allemand d'Échanges Universitaires)",
        "location": "Allemagne",
        "url":      "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
        "deadline": "Octobre / Novembre (chaque année)",
        "desc":     "Bourses complètes pour masters en Allemagne — très forte demande en informatique et IA.",
        "tags":     ["IADATA", "DSI", "CIR"],
        "gpa_min":  14.0,
    },
    # ── Erasmus+ ──────────────────────────────────────────────────────────────
    {
        "title":    "Erasmus+ Mundus — Joint Master Degree",
        "company":  "Union Européenne",
        "location": "Europe",
        "url":      "https://erasmus-plus.ec.europa.eu/opportunities/individuals/students/erasmus-mundus-joint-masters",
        "deadline": "Janvier (selon programme)",
        "desc":     "Programme de masters conjoints entre plusieurs universités européennes avec bourse complète.",
        "tags":     ["IADATA", "DSI", "CIR"],
        "gpa_min":  13.5,
    },
    # ── Fulbright (USA) ───────────────────────────────────────────────────────
    {
        "title":    "Fulbright Foreign Student Program",
        "company":  "Commission Maroco-Américaine pour les Échanges Éducatifs",
        "location": "États-Unis",
        "url":      "https://www.macece.ma/fulbright-foreign-student-program/",
        "deadline": "Mai (chaque année)",
        "desc":     "Bourse pour masters et doctorats aux USA. Couvre scolarité, logement et billet d'avion.",
        "tags":     ["IADATA", "DSI", "CIR"],
        "gpa_min":  15.0,
    },
    # ── IA / Data Science spécifiques ────────────────────────────────────────
    {
        "title":    "Google PhD Fellowship — AI & Machine Learning",
        "company":  "Google",
        "location": "International (remote eligible)",
        "url":      "https://research.google/outreach/phd-fellowship/",
        "deadline": "Décembre (chaque année)",
        "desc":     "Bourse Google pour recherche en IA, ML, Systèmes distribués et NLP.",
        "tags":     ["IADATA"],
        "gpa_min":  15.0,
    },
    {
        "title":    "Microsoft Research PhD Fellowship",
        "company":  "Microsoft Research",
        "location": "International",
        "url":      "https://www.microsoft.com/en-us/research/academic-program/phd-fellowship/",
        "deadline": "Septembre (chaque année)",
        "desc":     "Soutien financier et mentorat pour doctorants en informatique et IA.",
        "tags":     ["IADATA", "DSI"],
        "gpa_min":  15.0,
    },
    # ── Cybersécurité spécifiques ─────────────────────────────────────────────
    {
        "title":    "Bourse ENISA — Cybersécurité Europe",
        "company":  "Agence de l'Union Européenne pour la Cybersécurité",
        "location": "Europe",
        "url":      "https://www.enisa.europa.eu/topics/education/scholarships",
        "deadline": "Variable",
        "desc":     "Bourses et stages pour étudiants spécialisés en cybersécurité au sein de l'UE.",
        "tags":     ["CIR"],
        "gpa_min":  13.0,
    },
    # ── DSI / Software Engineering spécifiques ────────────────────────────────
    {
        "title":    "OCP Foundation — Bourses Excellence Maroc",
        "company":  "OCP Group",
        "location": "Maroc",
        "url":      "https://www.ocpfoundation.ma/bourses",
        "deadline": "Juillet (chaque année)",
        "desc":     "Bourses pour étudiants marocains excellents dans les filières scientifiques et techniques.",
        "tags":     ["IADATA", "DSI", "CIR"],
        "gpa_min":  14.5,
    },
    {
        "title":    "Bourse INWI — Talents du Numérique",
        "company":  "INWI Maroc",
        "location": "Maroc",
        "url":      "https://www.inwi.ma/fr/inwi/responsabilite-societale",
        "deadline": "Variable",
        "desc":     "Programme d'accompagnement et de financement pour jeunes talents du numérique au Maroc.",
        "tags":     ["DSI", "CIR"],
        "gpa_min":  13.0,
    },
]


def _get_scholarships(branch: str, gpa: float) -> list[Opportunity]:
    """Return scholarships matching the branch and student's GPA."""
    results = []
    for s in _SCHOLARSHIPS:
        if branch not in s["tags"]:
            continue
        if gpa < s["gpa_min"]:
            continue
        results.append(Opportunity(
            title       = s["title"],
            company     = s["company"],
            location    = s["location"],
            url         = s["url"],
            source      = "Base de données curatée",
            kind        = "scholarship",
            description = s["desc"],
            deadline    = s["deadline"],
            tags        = s["tags"],
        ))
    return results

# ── Main recommendation function ──────────────────────────────────────────────

def recommend_opportunities(
    predicted_branch: str,
    gpa: float = 0.0,
    max_internships: int = 6,
) -> dict[str, list[Opportunity]]:
    """
    Main entry point.

    Parameters
    ----------
    predicted_branch : str
        One of "IADATA", "DSI", "CIR"
    gpa : float
        Student's average grade (out of 20). Used to filter scholarships.
    max_internships : int
        Maximum number of internship results to return.

    Returns
    -------
    dict with keys "stages" and "scholarships", each a list of Opportunity objects.
    """
    keywords  = BRANCH_KEYWORDS.get(predicted_branch, [])
    stages: list[Opportunity] = []

    # Try Rekrute first
    rekrute_results = _scrape_rekrute(keywords, max_results=max_internships)
    stages.extend(rekrute_results)

    # If Rekrute returned nothing, fall back to Emploi.ma
    if not stages:
        emploi_results = _scrape_emploima(keywords, max_results=max_internships)
        stages.extend(emploi_results)

    scholarships = _get_scholarships(predicted_branch, gpa)

    return {
        "stages":       stages,
        "scholarships": scholarships,
    }


def to_dataframe(opportunities: list[Opportunity]) -> pd.DataFrame:
    """Convert a list of Opportunity objects to a Pandas DataFrame."""
    if not opportunities:
        return pd.DataFrame()
    return pd.DataFrame([o.to_dict() for o in opportunities])
