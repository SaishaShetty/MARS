import random

# Knowledge levels to match reviewers with appropriate expertise
knowledge_levels = [
    "Novice",         # Limited understanding of the field
    "Intermediate",   # Familiar with core concepts
    "Advanced",       # Strong grasp of the subject
    "Expert"          # Recognized authority in the field
]

# Tone of feedback that the reviewer might provide
tones = [
    "Supportive",    # Positive and encouraging feedback
    "Neutral",       # Objective and factual feedback
    "Critical",      # Focused on flaws and weaknesses
    "Harsh",         # Highly critical with minimal positive feedback
    "Diplomatic"     # Balanced critique with encouragement
]

# Experience levels to represent a reviewer's professional standing
experience_levels = [
    "an Early Career",    # Less experienced in reviewing
    "a Mid Career",      # More established with several publications
    "a Senior Career",          # Highly experienced with significant expertise
    "a Distinguished Leader"           # Recognized leader in the field, often invited for prestigious reviews
]

# Conflict of interest categories (to avoid bias)
conflict_of_interest = [
    "None",           # No conflicts of interest
    "Colleague",      # A colleague or collaborator with the author
    "Mentor/Mentee",  # A mentor or mentee relationship with the author
    "Personal",       # Personal relationship with the author
    "Professional"    # Professional competition or rivalry with the author
]

# Review decisions based on the quality of the paper
decisions = [
    "Accept",                    # The paper is of high quality and valuable
    "WeakAccept",           # The paper needs small improvements or clarifications
    "WeakReject",           # The paper requires significant changes
    "Reject",                    # The paper is not suitable for publication
]

class Reviewer:
    def __init__(self, name):
        self.name = name
        self.knowledge_level = random.choice(knowledge_levels)
        self.experience_level = random.choice(experience_levels)
        self.tone = random.choice(tones)
        self.conflict_of_interest = random.choice(conflict_of_interest)
        self.decisions = decisions

    def __str__(self):
        return f"{self.name} ({self.knowledge_level} - {self.experience_level} Reviewer, {self.tone} Feedback, Conflict: {self.conflict_of_interest}, Decisions: {self.decisions})"
    
    def __repr__(self):
        return f"Reviewer('{self.name}', '{self.knowledge_level}', '{self.experience_level}', '{self.tone}', '{self.conflict_of_interest}', '{self.decisions}')"

# Create a reviewer generator that yields random reviewers and stops only when 3 non-conflicted reviewers are found
def reviewer_generator():
    conflicted_reviewers = 0
    while conflicted_reviewers < 3:
        reviewer = Reviewer(f"Reviewer {random.randint(1, 100)}")
        if reviewer.conflict_of_interest == "None":
            conflicted_reviewers += 1
            yield reviewer

# Generate reviewers
all_reviewers = reviewer_generator()

# Collect reviewers with no conflicts of interest
non_conflicted_reviewers = [reviewer for reviewer in all_reviewers]

# for each reviewer, format a message that can be put into a SYSTEM message for an LLM
# the message will be in the format: "You are Reviewer {name}, who has been assigned to review a paper. You are an {experience_level} {knowledge_level} reviewer with a {tone} tone of feedback. You have no conflicts of interest. Your decisions may include: {decisions}"
# the message will be stored in a list called "reviewer_messages"
reviewer_messages = []
for reviewer in non_conflicted_reviewers:
    message = f"You are {reviewer.name}, who has been assigned to review a paper. You are {reviewer.experience_level} reviewer with {reviewer.knowledge_level} knowledge base and {reviewer.tone} tone of feedback. Your decisions may include: [{', '.join(reviewer.decisions)}]"
    reviewer_messages.append(message)
