class UserInfo:
    def __init__(self, name, age, knowledge_level):
        self.name = name
        self.age = age
        self.knowledge_level = knowledge_level

    def __str__(self):
        return f"UserInfo(Name: {self.name}, Age: {self.age}, Knowledge Level: {self.knowledge_level})"
    
    def setUserInfo(self, name, age, knowledge_level):
        self.name = name
        self.age = age
        self.knowledge_level = knowledge_level

    def getUserInfo(self):
        return f"Name: {self.name}, Age: {self.age}, Knowledge Level: {self.knowledge_level}"
    
    def QuestionsToSetKnowledgeLevel(self):
        pass;

