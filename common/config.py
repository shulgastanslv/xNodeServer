import tomli

class Config:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config = self.load()

    def load(self):
        try:
            with open(self.file_path, 'rb') as f:
                return tomli.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"The configuration file {self.file_path} was not found.")
        except tomli.TOMLDecodeError as e:
            raise ValueError(f"Error parsing TOML file {self.file_path}: {e}")

    def get(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            section, subsection = key
            return self.config.get(section, {}).get(subsection, None)
        return self.config.get(key, {})

    def __repr__(self):
        return f"{self.config}"

