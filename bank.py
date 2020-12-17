from errors import UnSuportedCard
from typed import Account, Card


class BaseBankAPI:
    def __init__(self, **kwargs):
        pass

    def check_card(self, card: Card):
        pass

    def check_pin_number(self, card: Card, pin_number: str) -> bool:
        pass

    def get_account_list(self, card: Card):
        pass

    def check_balance(self, account: Account):
        pass

    def withdraw(self, account: Account, amount: int):
        pass

    def deposit(self, account: Account, amount: int):
        pass


class MockBankAPI(BaseBankAPI):
    def __init__(self, init_data=None,**kwargs):
        '''
        sample of init_data
        init_data = {
            "<card_number>":{
                "pin":"<pin_number>",
                "accounts":{
                    "<account_id>":"<balance>"
                }
            }
        }
        '''
        super(MockBankAPI, self).__init__(**kwargs)
        self.data = init_data or {}
        self.accounts:dict = {}
        for card in self.data.values():
            self.accounts.update(card.get('accounts', {}))
        pass

    def check_card(self, card: Card):
        if not self.data.get(card.number):
            raise UnSuportedCard()

    def check_pin_number(self, card: Card, pin_number: str):
        return True if self.data.get(card.number, {}).get('pin') == pin_number else False

    def get_account_list(self, card: Card):
        accounts = self.data.get(card.number, {}).get('accounts', {})
        return [Account(id=a) for a in accounts.keys()]

    def check_balance(self, account: Account):
        return self.accounts[account.id]

    def withdraw(self, account: Account, amount: int):
        self.accounts[account.id] -= amount

    def deposit(self, account: Account, amount: int):
        self.accounts[account.id] += amount
