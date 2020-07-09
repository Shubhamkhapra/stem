"""
Unit tests for the stem.util.Synchronous class.
"""

import asyncio
import io
import unittest

from unittest.mock import patch, Mock

from stem.util import Synchronous
from stem.util.test_tools import coro_func_returning_value

EXAMPLE_OUTPUT = """\
hello from a synchronous context
hello from an asynchronous context
"""


class Example(Synchronous):
  async def hello(self):
    return 'hello'

  def sync_hello(self):
    return 'hello'

class TestSynchronous(unittest.TestCase):
  @patch('sys.stdout', new_callable = io.StringIO)
  def test_example(self, stdout_mock):
    """
    Run the example from our pydoc.
    """

    def sync_demo():
      instance = Example()
      print('%s from a synchronous context' % instance.hello())
      instance.stop()

    async def async_demo():
      instance = Example()
      print('%s from an asynchronous context' % await instance.hello())
      instance.stop()

    sync_demo()
    asyncio.run(async_demo())

    self.assertEqual(EXAMPLE_OUTPUT, stdout_mock.getvalue())

  def test_ainit(self):
    """
    Check that our constructor runs __ainit__ when present.
    """

    class AinitDemo(Synchronous):
      def __init__(self):
        super(AinitDemo, self).__init__()

      def __ainit__(self):
        self.ainit_loop = asyncio.get_running_loop()

    def sync_demo():
      instance = AinitDemo()
      self.assertTrue(hasattr(instance, 'ainit_loop'))

    async def async_demo():
      instance = AinitDemo()
      self.assertTrue(hasattr(instance, 'ainit_loop'))

    sync_demo()
    asyncio.run(async_demo())

  def test_after_stop(self):
    """
    Check that stopped instances raise a RuntimeError to synchronous callers.
    """

    # stop a used instance

    instance = Example()
    self.assertEqual('hello', instance.hello())
    instance.stop()
    self.assertRaises(RuntimeError, instance.hello)

    # stop an unused instance

    instance = Example()
    instance.stop()
    self.assertRaises(RuntimeError, instance.hello)

  def test_resuming(self):
    """
    Resume a previously stopped instance.
    """

    instance = Example()
    self.assertEqual('hello', instance.hello())
    instance.stop()
    self.assertRaises(RuntimeError, instance.hello)
    instance.start()
    self.assertEqual('hello', instance.hello())
    instance.stop()

  def test_asynchronous_mockability(self):
    """
    Check that method mocks are respected.
    """

    # mock prior to construction

    with patch('test.unit.util.synchronous.Example.hello', Mock(side_effect = coro_func_returning_value('mocked hello'))):
      instance = Example()
      self.assertEqual('mocked hello', instance.hello())

    self.assertEqual('hello', instance.hello())  # mock should now be reverted
    instance.stop()

    # mock after construction

    instance = Example()

    with patch('test.unit.util.synchronous.Example.hello', Mock(side_effect = coro_func_returning_value('mocked hello'))):
      self.assertEqual('mocked hello', instance.hello())

    self.assertEqual('hello', instance.hello())
    instance.stop()

  def test_synchronous_mockability(self):
    """
    Ensure we do not disrupt non-asynchronous method mocks.
    """

    # mock prior to construction

    with patch('test.unit.util.synchronous.Example.sync_hello', Mock(return_value = 'mocked hello')):
      instance = Example()
      self.assertEqual('mocked hello', instance.sync_hello())

    self.assertEqual('hello', instance.sync_hello())  # mock should now be reverted
    instance.stop()

    # mock after construction

    instance = Example()

    with patch('test.unit.util.synchronous.Example.sync_hello', Mock(return_value = 'mocked hello')):
      self.assertEqual('mocked hello', instance.sync_hello())

    self.assertEqual('hello', instance.sync_hello())
    instance.stop()
