class ParseCounter:
    def __init__(self):
        self.cards_parsed: set[str] = set()
        self.card_faces_parsed: set[tuple[str, str | None]] = set()
        self.card_printings_parsed: set[str] = set()
        self.card_face_printings_parsed: set[str] = set()
        self.card_localisations_parsed: set[tuple[str, str]] = set()
