class DataRecord:
    def __init__(self, user_id, email, region, plan, joined_at, last_seen, score=0):
        self.user_id = user_id
        self.email = email
        self.region = region
        self.plan = plan
        self.joined_at = joined_at
        self.last_seen = last_seen
        self.score = score
