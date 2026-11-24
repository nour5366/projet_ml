"""Le CONTRAT de l'API. Écrit avant le reste, il ne dépend d'aucun fournisseur.

Idée : une énumération (Enum) est une liste fermée de valeurs permises.
C'est comme un menu déroulant : on ne peut pas inventer une 7e valeur.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Sport(str, Enum):
    football = "football"
    basket = "basket"
    natation = "natation"
    course = "course"
    tennis = "tennis"
    volley = "volley"


class Intention(str, Enum):
    inscription = "inscription"    # l'utilisateur veut s'inscrire
    information = "information"    # il pose une question
    hors_sujet = "hors_sujet"      # rien à voir avec le sport


class Statut(str, Enum):
    inscrit = "inscrit"            # l'inscription a été créée
    refuse = "refuse"              # une règle ou un garde-fou a dit non
    a_verifier = "a_verifier"      # demande incomplète ou incertaine
    information = "information"    # simple réponse à une question


# ---------- Entrée et sortie de l'API ----------

class AssistantRequest(BaseModel):
    message: str = Field(min_length=3, max_length=500)


class Action(BaseModel):
    outil: str
    arguments: dict
    resultat: dict


class AssistantResponse(BaseModel):
    provider: str            # qui a répondu : mock ou le vrai fournisseur
    model: str               # quel modèle
    degrade: bool            # True si le mode réel a échoué et que le mock a pris le relais
    latency_ms: float        # temps de traitement mesuré
    intention: Intention
    statut: Statut
    confiance: float = Field(ge=0, le=1)
    reponse: str
    actions: list[Action]    # les outils appelés (utile pour le diagnostic)
    requires_review: bool    # True : un humain devrait regarder
    tours: int
    abandon: bool            # True : l'agent a atteint max_tours sans conclure


# ---------- Arguments des outils (bornes vérifiées par Pydantic) ----------

class ArgsListe(BaseModel):
    sport: Sport | None = None


class ArgsEligibilite(BaseModel):
    id_evenement: str = Field(pattern=r"^E\d{2}$")
    age: int = Field(ge=5, le=99)


class ArgsInscription(BaseModel):
    id_evenement: str = Field(pattern=r"^E\d{2}$")
    nom: str = Field(min_length=2, max_length=50)
    age: int = Field(ge=5, le=99)


# ── Schémas multimédia ────────────────────────────────────────────────────────

class MediaType(str, Enum):
    """Type général du fichier multimédia."""
    image = "image"
    audio = "audio"


class ImageFormat(str, Enum):
    """Format d'image pris en charge."""
    jpeg = "jpeg"
    png = "png"
    webp = "webp"


class AudioFormat(str, Enum):
    """Format audio pris en charge."""
    wav = "wav"
    mp3 = "mp3"
    m4a = "m4a"
    ogg = "ogg"


class MediaValidationResult(BaseModel):
    """Résultat de la validation d'un fichier multimédia (avant analyse)."""
    valide: bool
    media_type: Optional[MediaType] = None
    format_detecte: Optional[str] = None   # ex. "jpeg", "wav"
    taille_octets: int = 0
    erreur: Optional[str] = None           # message d'erreur si invalide


class MediaAnalysisResult(BaseModel):
    """Résultat de l'analyse multimédia par Gemini (ou le simulateur)."""
    media_type: MediaType
    format_detecte: str
    taille_octets: int
    texte_extrait: str           # description ou transcription
    confiance: float = Field(ge=0.0, le=1.0, default=1.0)
    mode: str                    # "real" ou "simule"
    metadata: dict = Field(default_factory=dict)  # infos supplémentaires

