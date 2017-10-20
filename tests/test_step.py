import unittest
import uuid

import core.config.config
import core.config.paths
from core.decorators import ActionResult
from core.executionelements.flag import Flag
from core.executionelements.nextstep import NextStep
from core.executionelements.step import Step, Widget
from core.helpers import UnknownApp, UnknownAppAction, InvalidInput, import_all_flags, import_all_filters
from core.appinstance import AppInstance
from tests.config import test_apps_path, function_api_path
import apps


class TestStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def setUp(self):
        self.uid = uuid.uuid4().hex
        self.basic_json = {'app': 'HelloWorld',
                           'action': 'helloWorld',
                           'device': '',
                           'name': '',
                           'next_steps': [],
                           'position': {},
                           'inputs': [],
                           'widgets': [],
                           'risk': 0,
                           'uid': self.uid}
        self.basic_input_json = {'app': 'HelloWorld',
                                 'action': 'helloWorld',
                                 'name': '',
                                 'next_steps': [],
                                 'position': {},
                                 'inputs': [],
                                 'uid': self.uid}

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, elem, name, action, app, device, inputs, next_steps,
                       widgets, risk=0., position=None, uid=None):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.action, action)
        self.assertEqual(elem.app, app)
        self.assertEqual(elem.device, device)
        self.assertDictEqual({key: input_element for key, input_element in elem.inputs.items()}, inputs)
        self.assertListEqual([conditional.read() for conditional in elem.next_steps], next_steps)
        self.assertEqual(elem.risk, risk)
        widgets = [Widget(app, widget) for (app, widget) in widgets]
        self.assertEqual(len(elem.widgets), len(widgets))
        for widget in elem.widgets:
            found = next((widget_ for widget_ in widgets if widget.app == widget_.app and widget.name == widget_.name), None)
            self.assertIsNotNone(found)
        position = position if position is not None else {}
        self.assertDictEqual(elem.position, position)
        self.assertIsNone(elem.get_output())
        self.assertFalse(elem.templated)
        if uid is None:
            self.assertIsNotNone(elem.uid)
        else:
            self.assertEqual(elem.uid, uid)

    def test_init_app_and_action_only(self):
        step = Step(app='HelloWorld', action='helloWorld')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        step = Step(app='HelloWorld', action='helloWorld', uid=uid)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], uid=uid)

    def test_init_app_and_action_name_different_than_method_name(self):
        step = Step(app='HelloWorld', action='Hello World')
        self.__compare_init(step, '', 'Hello World', 'HelloWorld', '', {}, [], [])

    def test_init_invalid_app(self):
        with self.assertRaises(UnknownApp):
            Step(app='InvalidApp', action='helloWorld')

    def test_init_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            Step(app='HelloWorld', action='invalid')

    def test_init_with_inputs_no_conversion(self):
        step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': -5.6})
        self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [])

    def test_init_with_inputs_with_conversion(self):
        step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': '-5.6'})
        self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [])

    def test_init_with_invalid_input_name(self):
        with self.assertRaises(InvalidInput):
            Step(app='HelloWorld', action='returnPlusOne', inputs={'invalid': '-5.6'})

    def test_init_with_invalid_input_type(self):
        with self.assertRaises(InvalidInput):
            Step(app='HelloWorld', action='returnPlusOne', inputs={'number': 'invalid'})

    def test_init_with_name(self):
        step = Step(app='HelloWorld', action='helloWorld', name='name')
        self.__compare_init(step, 'name', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_init_with_device(self):
        step = Step(app='HelloWorld', action='helloWorld', device='dev')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', 'dev', {}, [], [])

    def test_init_with_none_device(self):
        step = Step(app='HelloWorld', action='helloWorld', device='None')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_init_with_risk(self):
        step = Step(app='HelloWorld', action='helloWorld', risk=42.3)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], risk=42.3)

    def test_init_with_widgets(self):
        widget_tuples = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        widgets = [{'app': widget[0], 'name': widget[1]} for widget in widget_tuples]
        step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], widget_tuples)

    def test_init_with_widget_objects(self):
        widget_tuples = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        widgets = [Widget(*widget) for widget in widget_tuples]
        step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], widget_tuples)

    def test_init_with_position(self):
        step = Step(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], position={'x': -12.3, 'y': 485})

    def test_init_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [step.read() for step in next_steps], [])

    def test_execute_no_args(self):
        step = Step(app='HelloWorld', action='helloWorld')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        self.assertEqual(step.execute(instance.instance, {}), ActionResult({'message': 'HELLO WORLD'}, 'Success'))
        self.assertEqual(step._output, ActionResult({'message': 'HELLO WORLD'}, 'Success'))

    def test_execute_with_args(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_with_accumulator_with_conversion(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_with_accumulator_with_extra_steps(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_with_accumulator_missing_step(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(InvalidInput):
            step.execute(instance.instance, accumulator)

    def test_execute_with_complex_inputs(self):
        step = Step(app='HelloWorld', action='Json Sample',
                    inputs={'json_in': {'a': '-5.6', 'b': {'a': '4.3', 'b': 5.3}, 'c': ['1', '2', '3'],
                                        'd': [{'a': '', 'b': 3}, {'a': '', 'b': -1.5}, {'a': '', 'b': -0.5}]}})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 11.0)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_action_which_raises_exception(self):
        from tests.apps.HelloWorld.exceptions import CustomException
        step = Step(app='HelloWorld', action='Buggy')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(CustomException):
            step.execute(instance.instance, {})

    def test_execute_event(self):
        step = Step(app='HelloWorld', action='Sample Event', inputs={'arg1': 1})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        import time
        from tests.apps.HelloWorld.events import event1
        import threading

        def sender():
            time.sleep(0.1)
            event1.trigger(3)

        thread = threading.Thread(target=sender)
        start = time.time()
        thread.start()
        result = step.execute(instance.instance, {})
        end = time.time()
        thread.join()
        self.assertEqual(result, ActionResult(4, 'Success'))
        self.assertGreater((end-start), 0.1)

    def test_get_next_step_no_next_steps(self):
        step = Step(app='HelloWorld', action='helloWorld')
        step._output = 'something'
        self.assertIsNone(step.get_next_step({}))

    def test_get_next_step(self):
        flag1 = [Flag(action='mod1_flag2', args={'arg1': '3'}), Flag(action='mod1_flag2', args={'arg1': '-1'})]
        next_steps = [NextStep(flags=flag1, name='name1'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        step._output = ActionResult(2, 'Success')
        self.assertEqual(step.get_next_step({}), 'name2')
        step._output = ActionResult(1, 'Success')
        self.assertEqual(step.get_next_step({}), 'name1')

    def test_set_input_valid(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        step.set_input({'num1': '-5.62', 'num2': '5', 'num3': '42.42'})
        self.assertDictEqual(step.inputs, {'num1': -5.62, 'num2': 5., 'num3': 42.42})

    def test_set_input_invalid_name(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'invalid': '5', 'num3': '42.42'})

    def test_set_input_invalid_format(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'num2': '5', 'num3': 'invalid'})
