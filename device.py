import logging

logger = logging.getLogger(__name__)


class BaseDeviceAPI:

    def __init__(self, **kwargs):
        pass

    def withdraw_available(self, amount: int) -> bool:
        pass

    def withdraw(self, amount: int):
        pass

    def deposit(self) -> int:
        pass

    def card_eject(self):
        pass


class MockDeviceAPI(BaseDeviceAPI):
    def __init__(self, deposit_amount: int = 1000,cache=2000, **kwargs):
        super(MockDeviceAPI, self).__init__(**kwargs)
        self.cache = cache
        self.deposit_amount = deposit_amount

    def withdraw_available(self, amount: int) -> bool:
        return True if self.cache >= amount else False

    def withdraw(self, amount: int):
        self.cache -= amount

    def deposit(self) -> int:
        return self.deposit_amount

    def card_eject(self):
        logger.debug('card ejected')
        pass
