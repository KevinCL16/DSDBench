from abc import ABC, abstractmethod

class GenericAgent(ABC):
    def __init__(self, workspace, **kwargs):
        self.workspace = workspace
        self.prompts = kwargs.get('prompts', {})

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def get_prompt(self, prompt_type):
        return self.prompts.get(prompt_type, '')