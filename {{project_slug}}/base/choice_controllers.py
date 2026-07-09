from abc import ABC
from inspect import isclass

from django.db.models import Choices
from django.utils.module_loading import import_string

from django.conf import settings
from django.db.models import Model
from django.apps import apps
from django.db.models import QuerySet, Q, Model
from django.db.models import Max

from rest_framework.exceptions import NotFound, ValidationError


__ALL__ = [
    'ChoiceControllerAbstact',
    'ModelChoiceController',
    'EnumChoiceController'
]

"""
======================================================================

DRC_MODEL_CHOICES_SETTING <dict> is constant to setting model that want to have in choice api
    and set controller for each choice. If not set it will use controller from `DRC_DEFAULT_CHOICES_CONTROLLER`
    by formate 
        <model_key>: {
            "app": <django app name>,
            "model": <django model name>
        }
    Ex.
    DRC_MODEL_CHOICES_SETTING = {
        "tag": {
            "app": "todo_list",
            "model": "Tag"
        },
        "task": {
            "app": "todo_list",
            "model": "Task",
            "controller": TaskChoiceController  #diract class define 
        },
        "sub_task": {
            "app": "todo_list",
            "model": "SubTask",
            "controller": "todo_list.choices.SubTaskChoiceController"  #string import
        },
    }

======================================================================

DRC_DEFAULT_CHOICES_CONTROLLER <string path> is default controller for choice api
    it can be set by string path or diract class.

======================================================================

DRC_DEFAULT_INFORMATION_FORMAT <function> is default format choice information

======================================================================

DRC_MODEL_INFORMATION_PROPERTY <string> is property name that store choice information in model
    default is `choices_information`

======================================================================
"""

def _default_information_format(object: Model, *args, **kwargs) -> dict:
    return {
        "value": object.pk,
        "label": str(object),
    }

def get_default_controller(choice_type):
    default_controller = "{{project_slug}}.base.choice_controllers.ModelChoiceController"
    if choice_type == 'enum':
        default_controller = "{{project_slug}}.base.choice_controllers.EnumChoiceController"
    return getattr(
        settings, 'DRC_DEFAULT_CHOICES_CONTROLLER', default_controller
    )

def get_default_information_format():
    return getattr(settings, 'DRC_DEFAULT_INFORMATION_FORMAT', _default_information_format)

def get_choices_setting():
    return getattr(settings, 'DRC_MODEL_CHOICES_SETTING', {})

def get_model_information_property():
    return getattr(settings, 'DRC_MODEL_INFORMATION_PROPERTY', 'choices_information')

def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import %r for setting %r. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)

def perform_import_controller(val, setting_name, choice_type: str='model'):
    """
    If the given setting is a string import notation,
    """
    default_controller = get_default_controller(choice_type)
    val = val or default_controller
    if isinstance(val, str):
        _class = import_from_string(val, setting_name)
    elif isclass(val):
        _class = val
    else:
        raise ValueError("settings value must be string or class.")
    
    if not issubclass(_class, ChoiceControllerAbstact):
        raise ValueError("settings value must be subclass of ChoiceControllerAbstact.")
    return _class

def perform_import_choice_class(val, setting_name) -> Choices:
    if isinstance(val, str):
        _class = import_from_string(val, setting_name)
    elif isclass(val):
        _class = val
    else:
        raise ValueError("settings value must be string or class.")
    
    if not issubclass(_class, Choices):
        raise ValueError("settings value must be subclass of Choices.")
    return _class


def get_choices_information(object, *args, **kwargs) -> dict:
    MODEL_INFORMATION_PROPERTY = get_model_information_property()
    if hasattr(object, MODEL_INFORMATION_PROPERTY):
        _information_format = getattr(object, MODEL_INFORMATION_PROPERTY, {})
    else:
        _information_format_func = get_default_information_format()
        if callable(_information_format_func):
            _information_format =  _information_format_func(object, *args, **kwargs)
        else:
            raise ValueError(f"Object {object} does not have a valid {MODEL_INFORMATION_PROPERTY} property.")

    return _information_format


class ChoiceControllerAbstact(ABC):

    @property
    def data(self) -> list:
        return []


class ModelChoiceController(ChoiceControllerAbstact):
    """
    Base class for handling choice-related operations.

    Flow:
        0. call `data` method
        1. Retrieve the initial queryset using `get_choice_queryset`.
        2. Apply filters to the queryset using `get_filter_query` and `get_filterset`.
        3. Convert the filtered queryset into a list of choice representations using `get_representation_data`.
        4. Sort the choice representations using `sort_choice_output`.
        5. Return the sorted and filtered choice data.

    Attributes:
        choice_key (str): The key representing the choice.
        app_model (Model): The Django model associated with the choice.
        request (Request): The current request object.
        queryset (QuerySet): The queryset for the model.
        sort_key (str): The key used for sorting the choices.
        extra_key (list): Additional keys to include in the choice representation.
        filter (dict): Filters to apply to the queryset.

    Methods:
        data: Returns the sorted and filtered choice data.
        get_choice_queryset: Returns the initial queryset for the choice.
        get_filterset: Constructs the filter set for the queryset.
        get_filter_query: Applies the filter set to the queryset.
        get_representation_data: Converts the queryset into a list of choice representations.
        get_extra_set: Retrieves additional keys for a choice object.
        sort_choice_output: Sorts the choice output based on the sort key.
    """

    choice_key = None
    app_model = None
    request = None
    queryset = None
    sort_key = ''
    extra_key = list()
    filter = dict()

    def __init__(self, key:str, filter:dict, extra_key:list , choice_info:dict, request=None, *args, **kwargs) -> None:

        self.choice_key = key
        self.filter = filter
        self.extra_key = extra_key
        self.extra_key.extend(choice_info.get('extra_key', []))
        self.sort_key = choice_info.get('sort', 'label')

        self.app_name = choice_info.get('app')
        self.model_name = choice_info.get('model')
        self.app_model = apps.get_model(self.app_name, self.model_name)

        self.request = request

    @property
    def data(self):
        queryset = self.get_choice_queryset()
        queryset = self.get_filter_query(queryset, self.get_filterset())
        datas = self.get_representation_data(queryset)
        datas = self.sort_choice_output(datas)
        return datas

    def get_choice_queryset(self) -> QuerySet:
        queryset = self.app_model.objects.all()
        return queryset

    def get_filterset(self) -> Q:
        filter_set = Q()
        for key, value in self.filter.items():
            if hasattr(self.app_model, key):
                if key.startswith('~'):
                    filter_set.add(~Q(**{key[1:]:value}), Q.AND)
                else:
                    filter_set.add(Q(**{key:value}), Q.AND)
        return filter_set

    def get_filter_query(self, queryset:QuerySet, filter_set:Q) -> QuerySet:
        return queryset.filter(filter_set).distinct()

    def get_representation_data(self, queryset) -> list:
        obj_list = []
        for obj in queryset:
            extra_key = self.get_extra_set(obj)
            context = {**get_choices_information(obj), **extra_key}
            obj_list.append(context)
        return obj_list

    def get_extra_set(self, obj) -> dict:
        extra_key = {}
        for key in self.extra_key:
            if hasattr(type(obj), key):
                ref = getattr(obj, key, None)
                if isinstance(ref, Model):
                    extra_key.update({key: getattr(ref, 'id', None)})
                else:
                    extra_key.update({key: ref})
        return extra_key

    def sort_choice_output(self, output: list) -> list:
        output.sort(key=lambda x: x[self.sort_key], reverse=False)
        return output


class EnumChoiceController(ChoiceControllerAbstact):
    """
    Base class for handling choice-related operations.

    Flow:
        0. call `data` method
        1. Import the choice class using `import_choices`.
        2. Retrieve the choice data using `get_representation_data`.
        3. Filter the choice data based on the filterset using `get_filter_datas`.
        4. Return the filtered choice data.

    Attributes:
        choice_key (str): The key representing the choice.
        choice_class_name (str): The name of the choice class.
        request (Request): The current request object.
        sort_key (str): The key used for sorting the choices.
        extra_key (list): Additional keys to include in the choice representation.
        filter (dict): Filters to apply to the choice data.

    Methods:
        data: Returns the filtered choice data.
        import_choices: Imports the choice class.
        get_filter_datas: Filters the choice data based on the filterset.
        get_filterset: Constructs the filter set for the choice data.
        get_extra_set: Retrieves additional keys for a choice object.
        get_representation_data: Converts the choice data into a list of representations.
    """

    choice_class_name = None
    choice_class = None
    choice_key = None
    request = None
    sort_key = ''
    extra_key = list()
    filter = dict()

    def __init__(self, key:str, filter:dict, extra_key:list , choice_info:dict, request=None, *args, **kwargs) -> None:
        self.choice_key = key
        self.filter = filter
        self.extra_key = extra_key
        self.extra_key.extend(choice_info.get('extra_key', []))
        self.sort_key = choice_info.get('sort', 'label')
        self.choice_class_name = choice_info.get('choice_class', None)
        self.request = request

    @property
    def data(self):
        self.import_choices()
        datas = self.get_representation_data()
        datas = self.get_filter_datas(datas, self.get_filterset())
        return datas

    def get_filter_datas(self, datas, filterset:dict):
        for key, value in filterset.items():
            datas = list(filter(lambda x, lkey=key, lvalue=value: lkey in x.keys() and x[lkey] == lvalue, datas))
        return datas

    def get_filterset(self):
        return {key: value for key, value in self.filter.items()}

    def import_choices(self):
        self.choice_class = perform_import_choice_class(self.choice_class_name, self.choice_key)

    def get_representation_data(self) -> list:
        obj_list = []
        for obj in self.choice_class:
            extra_key = self.get_extra_set(obj)
            context = {**get_choices_information(obj), **extra_key}
            obj_list.append(context)
        return obj_list

    def get_extra_set(self, obj) -> dict:
        extra_key = {}
        for key in self.extra_key:
            if hasattr(obj, key):
                ref = getattr(obj, key, None)
                extra_key.update({key: ref})
        return extra_key
