from re import sub


class NormalizeString:
    def __init__(self, string_to_normalize: str="") -> None:
        self.normalize_me = string_to_normalize
        self.normalize()
    
    def normalize(self):
        return " ".join(sub(r'[<>:!"/\\|?*]', '', self.normalize_me)
                        .strip()
                        .replace('\t', '')
                        .replace('\n', '')
                        .replace('.', '')
                        .split(' '))