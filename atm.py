import logging
from typing import List, Optional

from statemachine import State, StateMachine

from errors import InvalidAccount, InvalidPinNumber, InvalidRequest, NotEnoughMoney, UnSuportedCard
from typed import Account, Card

logger = logging.getLogger(__name__)


def mask_card_number(card_number: str):
    masked = ['*' for _ in len(card_number[4:])]
    return card_number[:4] + ''.join(masked)


#
class ATMStateMachine(StateMachine):
    """
    This class is strongly protects the condition of the atm device.
    Prevent unauthorized requests from being made arbitrarily.
    """
    ## State
    ready = State('Ready', initial=True)
    card_inserted = State('CardInserted')
    pin_checked = State('PinChecked')
    account_selected = State('AccountSelected')
    error = State('Error')

    ## Action
    insert_card = ready.to(card_inserted)
    check_pin_number = insert_card.to(pin_checked)
    get_account_list = check_pin_number.to(check_pin_number)
    select_account = pin_checked.to(account_selected)

    check_balance = account_selected.to(account_selected)
    deposit = account_selected.to(account_selected)
    withdraw = account_selected.to(account_selected)

    finish = card_inserted.to(ready) | pin_checked.to(ready) | account_selected.to(ready)
    need_fix = ready.to(error)


class BaseAtmAPI():
    def __init__(self, **kwargs):
        self.state = 'ready'
        self.state_machine = ATMStateMachine(self)

    def insert_card(self, **kwargs):
        self.state_machine.insert_card()

    def check_pin_number(self, **kwargs):
        self.state_machine.check_pin_number()

    def get_account_list(self, **kwargs):
        if not self.state_machine.is_pin_checked:
            raise InvalidRequest()

    def select_account(self, **kwargs):
        self.state_machine.select_account()

    def check_balance(self, **kwargs):
        self.state_machine.check_balance()

    def withdraw(self, **kwargs):
        self.state_machine.withdraw()

    def deposit(self, **kwargs):
        self.state_machine.deposit()

    def finish(self, **kwargs):
        self.state_machine.finish()


class ATM(BaseAtmAPI):

    def __init__(self, device_api=None, bank_api=None, **kwargs):
        super(ATM, self).__init__(**kwargs)
        self.device = device_api
        self.bank = bank_api

        self.card: Optional[Card] = None
        self._account_list: Optional[List[Account]] = None
        self.account: Optional[Account] = None

    def insert_card(self, card_data):
        super(ATM, self).insert_card()

        self.card = Card(**card_data)
        logger.debug(f'card<{mask_card_number(self.card.number)}> is inserted')

        try:
            self.bank.check_card(self.card)
        except Exception as e:
            logger.debug(f'card<{mask_card_number(self.card.number)}> have problems')
            logger.exception(e)
            self.finish()
            raise UnSuportedCard()

    def check_pin_number(self, pin_number):
        super(ATM, self).check_pin_number()

        if not self.bank.check_pin_number(self.card, pin_number):
            logger.debug(f'card<{mask_card_number(self.card.number)}> pin number is not collect')
            self.finish()
            raise InvalidPinNumber()

    def get_account_list(self) -> List[Account]:
        super(ATM, self).get_account_list()
        self._account_list = self.bank.get_account_list(self.card)
        return self._account_list

    def select_account(self, account: Account):
        super(ATM, self).select_account()
        if account not in self._account_list:
            raise InvalidAccount()
        self.account = account

    def check_balance(self, **kwargs) -> int:
        super().check_balance(**kwargs)
        return self.bank.check_balance(self.account)

    def withdraw(self, amount:int):
        super().withdraw()
        if not self.device.withdraw_avaliable(amount):
            raise NotEnoughMoney()

        if self.bank.withdraw(self.account, amount):
            self.device.withdraw(amount)

    def deposit(self):
        super().deposit()
        amount = self.device.deposit()
        try:
            self.bank.deposit(self.account, amount)
        except Exception as e:
            logger.exception(e)
            self.device.withdraw(amount)
        logger.debug(f'{self.account} deposit successfully')

    def _reset_data(self):
        self.card = None
        self._account_list = None
        self.account = None

    def finish(self):
        super(ATM, self).finish()
        try:
            self.device.card_eject()
            logger.debug(f'card<{mask_card_number(self.card.number)}> is eject')
            self._reset_data()
        except Exception as e:
            logger.exception(e)
            self.state_machine.need_fix()
