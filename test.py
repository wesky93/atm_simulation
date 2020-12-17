import unittest

from atm import ATM, BaseAtmAPI
from bank import MockBankAPI
from device import MockDeviceAPI
from errors import CardEjectFail, InvalidAccount, InvalidPinNumber, NotEnoughMoney, UnSuportedCard
from typed import Account


class TransactionTestCase(unittest.TestCase):

    def setUp(self):
        self.atm = BaseAtmAPI()

    def test_transaction(self):
        self.assertEqual(self.atm.state, 'ready')

        self.atm.insert_card()
        self.assertEqual(self.atm.state, 'card_inserted')

        self.atm.check_pin_number()
        self.assertEqual(self.atm.state, 'pin_checked')

        self.atm.get_account_list()
        self.assertEqual(self.atm.state, 'pin_checked')

        self.atm.select_account()
        self.assertEqual(self.atm.state, 'account_selected')

        self.atm.check_balance()
        self.assertEqual(self.atm.state, 'account_selected')

        self.atm.deposit()
        self.assertEqual(self.atm.state, 'account_selected')

        self.atm.withdraw()
        self.assertEqual(self.atm.state, 'account_selected')

        self.atm.finish()
        self.assertEqual(self.atm.state, 'ready')

        self.atm.need_fix()
        self.assertTrue(self.atm.state, 'error')


class BaseMockAtmTestCase(unittest.TestCase):

    def setUp(self):
        device_api = MockDeviceAPI(deposit_amount=2000, cache=2000)
        mock_data = {
            '1111-2222-3333-4444': {
                "pin": "12345",
                "accounts": {
                    "98765432": 5000,
                    "12345678": 1000,
                }
            }
        }
        bank_api = MockBankAPI(mock_data)

        self.atm = ATM(device_api, bank_api)

    def assertStateIsReady(self):
        self.assertEqual(self.atm.state, 'ready')

    def assertStateIsCardInserted(self):
        self.assertEqual(self.atm.state, 'card_inserted')

    def assertStateIsPinChecked(self):
        self.assertEqual(self.atm.state, 'pin_checked')

    def assertStateIsAccountSelected(self):
        self.assertEqual(self.atm.state, 'account_selected')

    def assertStateIsError(self):
        self.assertEqual(self.atm.state, 'error')

    def assertDataIsEmpty(self):
        self.assertIsNone(self.atm.card)
        self.assertIsNone(self.atm._account_list)
        self.assertIsNone(self.atm.account)


class InsertCardTestCase(BaseMockAtmTestCase):
    def test_ok(self):
        card_number = '1111-2222-3333-4444'

        self.atm.insert_card(card_number)

        self.assertStateIsCardInserted()

    def test_fail(self):
        card_number = '1234-1234-3333-4444'

        with self.assertRaises(UnSuportedCard):
            self.atm.insert_card(card_number)

        self.assertStateIsReady()


class CheckPinNumberTestCase(BaseMockAtmTestCase):

    def setUp(self):
        super(CheckPinNumberTestCase, self).setUp()
        card_number = '1111-2222-3333-4444'
        self.atm.insert_card(card_number)

    def test_ok(self):
        pin_number = '12345'

        self.atm.check_pin_number(pin_number)

        self.assertStateIsPinChecked()

    def test_fail(self):
        pin_number = '00000'

        with self.assertRaises(InvalidPinNumber):
            self.atm.check_pin_number(pin_number)

        self.assertStateIsReady()


class AccountTestCase(BaseMockAtmTestCase):

    def setUp(self):
        super(AccountTestCase, self).setUp()
        card_number = '1111-2222-3333-4444'
        pin_number = '12345'
        self.atm.insert_card(card_number)
        self.atm.check_pin_number(pin_number)

    def test_ok(self):
        accounts = self.atm.get_account_list()
        self.assertEqual({account.id for account in accounts}, {'98765432', '12345678'})

        self.atm.select_account(accounts[0])
        self.assertStateIsAccountSelected()

    def test_fail(self):
        self.atm.get_account_list()

        with self.assertRaises(InvalidAccount):
            self.atm.select_account(Account(id='12345'))
        self.assertStateIsPinChecked()


class AccountTransactionTestCase(BaseMockAtmTestCase):

    def setUp(self):
        super(AccountTransactionTestCase, self).setUp()
        card_number = '1111-2222-3333-4444'
        pin_number = '12345'
        self.atm.insert_card(card_number)
        self.atm.check_pin_number(pin_number)
        self.atm.get_account_list()
        self.account_5000 = Account(id='98765432')
        self.account_1000 = Account(id='12345678')

    def test_check_balance(self):
        self.atm.select_account(self.account_5000)
        self.assertEqual(5000, self.atm.check_balance())

    def test_withdraw_ok(self):
        self.atm.select_account(self.account_5000)
        self.atm.withdraw(2000)

        self.assertEqual(3000, self.atm.check_balance())

    def test_withdraw_fail_with_device(self):
        self.atm.select_account(self.account_5000)
        with self.assertRaises(NotEnoughMoney):
            self.atm.withdraw(4000)
        self.assertEqual(5000, self.atm.check_balance())

    def test_withdraw_fail_with_bank(self):
        self.atm.select_account(self.account_1000)
        with self.assertRaises(NotEnoughMoney):
            self.atm.withdraw(4000)
        self.assertEqual(1000, self.atm.check_balance())

    def test_deposit_ok(self):
        self.atm.select_account(self.account_1000)
        self.atm.deposit()
        self.assertEqual(3000, self.atm.check_balance())

    def test_finish_ok(self):
        self.atm.select_account(self.account_1000)
        self.atm.finish()

        self.assertDataIsEmpty()

    def test_finish_fail(self):
        def card_eject_fail():
            raise Exception()

        self.atm.device.card_eject = card_eject_fail

        self.atm.select_account(self.account_1000)
        with self.assertRaises(CardEjectFail):
            self.atm.finish()

        self.assertStateIsError()
        self.assertDataIsEmpty()

class IntegrationTestCase(BaseMockAtmTestCase):

    def test_integration(self):
        card_number = '1111-2222-3333-4444'
        pin_number = '12345'
        account_5000 = Account(id='98765432')

        self.assertStateIsReady()

        self.atm.insert_card(card_number)
        self.assertStateIsCardInserted()

        self.atm.check_pin_number(pin_number)
        self.assertStateIsPinChecked()


        self.assertTrue(account_5000 in self.atm.get_account_list())
        self.atm.select_account(account_5000)
        self.assertStateIsAccountSelected()

        self.assertEqual(5000, self.atm.check_balance())
        self.atm.withdraw(1000)
        self.assertEqual(4000, self.atm.check_balance())

        self.atm.deposit()
        self.assertEqual(6000, self.atm.check_balance())

        self.atm.finish()
        self.assertDataIsEmpty()







if __name__ == '__main__':
    unittest.main()
