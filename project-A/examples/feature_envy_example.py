class UserAccount:
    def __init__(self, balance, owner, status):
        self.balance = balance
        self.owner = owner
        self.status = status

class ReportGenerator:
    def __init__(self, account):
        self.account = account

    def generate_detailed_report(self):
        # Feature Envy: Too many calls to self.account
        acct = self.account
        summary = {
            "owner": acct.owner,
            "balance": acct.balance,
            "status": acct.status,
            "is_active": acct.status == "active",
            "projected_balance": acct.balance * 1.05,
        }
        return summary
