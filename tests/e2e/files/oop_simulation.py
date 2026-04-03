"""Bank account simulation exercising OOP: inheritance, properties, decorators."""


def validate_positive(fn):
    def wrapper(self, amount):
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        return fn(self, amount)

    return wrapper


class Transaction:
    def __init__(self, kind, amount, balance_after):
        self.kind = kind
        self.amount = amount
        self.balance_after = balance_after

    def __repr__(self):
        return (
            f"Transaction({self.kind}, {self.amount:.2f}, bal={self.balance_after:.2f})"
        )


class Account:
    _next_id = 1000

    def __init__(self, owner, initial_balance=0.0):
        self.owner = owner
        self._balance = float(initial_balance)
        self._history = []
        self.account_id = Account._next_id
        Account._next_id += 1

    @property
    def balance(self):
        return self._balance

    @validate_positive
    def deposit(self, amount):
        self._balance += amount
        self._history.append(Transaction("deposit", amount, self._balance))

    @validate_positive
    def withdraw(self, amount):
        if amount > self._balance:
            raise ValueError(
                f"Insufficient funds: need {amount:.2f}, have {self._balance:.2f}"
            )
        self._balance -= amount
        self._history.append(Transaction("withdraw", amount, self._balance))

    def statement(self):
        lines = [f"Account #{self.account_id} ({self.owner})"]
        for tx in self._history:
            lines.append(f"  {tx.kind:10s} {tx.amount:8.2f}  →  {tx.balance_after:.2f}")
        lines.append(f"  Balance: {self._balance:.2f}")
        return "\n".join(lines)

    def __repr__(self):
        return f"Account({self.owner!r}, balance={self._balance:.2f})"


class SavingsAccount(Account):
    def __init__(self, owner, initial_balance=0.0, rate=0.05):
        super().__init__(owner, initial_balance)
        self.rate = rate

    def apply_interest(self):
        interest = round(self._balance * self.rate, 2)
        if interest > 0:
            self.deposit(interest)
        return interest

    @validate_positive
    def withdraw(self, amount):
        penalty = 0.0
        if amount > self._balance * 0.5:
            penalty = round(amount * 0.02, 2)
        super().withdraw(amount)
        if penalty > 0:
            super().withdraw(penalty)


class CheckingAccount(Account):
    def __init__(self, owner, initial_balance=0.0, overdraft_limit=100.0):
        super().__init__(owner, initial_balance)
        self.overdraft_limit = overdraft_limit

    @validate_positive
    def withdraw(self, amount):
        if amount > self._balance + self.overdraft_limit:
            raise ValueError("Exceeds overdraft limit")
        self._balance -= amount
        self._history.append(Transaction("withdraw", amount, self._balance))


class Bank:
    def __init__(self, name):
        self.name = name
        self._accounts = {}

    def open(self, account):
        self._accounts[account.account_id] = account
        return account

    def transfer(self, from_id, to_id, amount):
        src = self._accounts[from_id]
        dst = self._accounts[to_id]
        src.withdraw(amount)
        dst.deposit(amount)

    def total_deposits(self):
        return sum(a.balance for a in self._accounts.values())

    def richest(self):
        return max(self._accounts.values(), key=lambda a: a.balance)

    def summary(self):
        lines = [f"Bank: {self.name}  ({len(self._accounts)} accounts)"]
        for acc in sorted(self._accounts.values(), key=lambda a: a.account_id):
            lines.append(f"  {acc}")
        lines.append(f"  Total deposits: {self.total_deposits():.2f}")
        return "\n".join(lines)


# ── Simulation ─────────────────────────────────────────────────────────────────

bank = Bank("PyBank")

alice = bank.open(Account("Alice", 500))
bob = bank.open(SavingsAccount("Bob", 1000, rate=0.10))
carol = bank.open(CheckingAccount("Carol", 200, overdraft_limit=150))

alice.deposit(300)
alice.withdraw(100)
bob.deposit(500)
interest = bob.apply_interest()
print(f"Bob interest: {interest:.2f}")
carol.deposit(50)
carol.withdraw(380)  # uses overdraft

bank.transfer(alice.account_id, bob.account_id, 200)
bank.transfer(bob.account_id, carol.account_id, 100)

print(bank.summary())
print("richest:", bank.richest().owner)

# Test error paths
errors = []
for desc, fn in [
    ("deposit zero", lambda: alice.deposit(0)),
    ("withdraw overdraft", lambda: carol.withdraw(500)),
]:
    try:
        fn()
    except ValueError:
        errors.append(f"{desc}: caught ValueError")
print("errors caught:", len(errors))
for e in errors:
    print(" ", e)

print(alice.statement())
print(bob.statement())

# Batch operations
accounts = [bank.open(Account(f"User{i}", i * 100)) for i in range(1, 6)]
for acc in accounts:
    acc.deposit(50)
    if acc.balance > 200:
        acc.withdraw(80)
totals = [acc.balance for acc in accounts]
print("batch balances:", totals)
print("batch total:", sum(totals))
