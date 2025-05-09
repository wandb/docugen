"""Documentation control decorators."""
import sys
from inspect import getmodule
from typing import Any, Iterable, TypeVar

import pydantic

T = TypeVar("T")

_DEPRECATED = "_docs_deprecated"


def set_deprecated(obj: T) -> T:
    """Explicitly tag an object as deprecated for the doc generator."""
    setattr(obj, _DEPRECATED, None)
    return obj


def is_deprecated(obj) -> bool:
    return hasattr(obj, _DEPRECATED)


_NO_SEARCH_HINTS = "_docs_no_search_hints"


def hide_from_search(obj: T) -> T:
    """Marks an object so metadata search hints will not be included on it's page.

    The page is set to "noindex" to hide it from search.

    Note: This only makes sense to apply to functions, classes and modules.
    Constants, and methods do not get their own pages.

    Args:
      obj: the object to hide.

    Returns:
      The object.
    """
    setattr(obj, _NO_SEARCH_HINTS, None)
    return obj


def should_hide_from_search(obj) -> bool:
    """Returns true if metadata search hints should not be included."""
    return hasattr(obj, _NO_SEARCH_HINTS)


_CUSTOM_PAGE_CONTENT = "_docs_custom_page_content"


def set_custom_page_content(obj, content):
    """Replace most of the generated page with custom content."""
    setattr(obj, _CUSTOM_PAGE_CONTENT, content)


def get_custom_page_content(obj):
    """Gets custom page content if available."""
    return getattr(obj, _CUSTOM_PAGE_CONTENT, None)


_DO_NOT_DOC = "_docs_do_not_document"


def do_not_generate_docs(obj: T) -> T:
    """A decorator: Do not generate docs for this object.

    For example the following classes:

    ```
    class Parent(object):
      def method1(self):
        pass
      def method2(self):
        pass

    class Child(Parent):
      def method1(self):
        pass
      def method2(self):
        pass
    ```

    Produce the following api_docs:

    ```
    /Parent.md
      # method1
      # method2
    /Child.md
      # method1
      # method2
    ```

    This decorator allows you to skip classes or methods:

    ```
    @do_not_generate_docs
    class Parent(object):
      def method1(self):
        pass
      def method2(self):
        pass

    class Child(Parent):
      @do_not_generate_docs
      def method1(self):
        pass
      def method2(self):
        pass
    ```

    This will only produce the following docs:

    ```
    /Child.md
      # method2
    ```

    Note: This is implemented by adding a hidden attribute on the object, so it
    cannot be used on objects which do not allow new attributes to be added. So
    this decorator must go *below* `@property`, `@classmethod`,
    or `@staticmethod`:

    ```
    class Example(object):
      @property
      @do_not_generate_docs
      def x(self):
        return self._x
    ```

    Args:
      obj: The object to hide from the generated docs.

    Returns:
      obj
    """
    setattr(obj, _DO_NOT_DOC, None)
    return obj


_DO_NOT_DOC_INHERITABLE = "_docs_do_not_doc_inheritable"


def do_not_doc_inheritable(obj: T) -> T:
    """A decorator: Do not generate docs for this method.

    This version of the decorator is "inherited" by subclasses. No docs will be
    generated for the decorated method in any subclass. Even if the sub-class
    overrides the method.

    For example, to ensure that `method1` is **never documented** use this
    decorator on the base-class:

    ```
    class Parent(object):
      @do_not_doc_inheritable
      def method1(self):
        pass
      def method2(self):
        pass

    class Child(Parent):
      def method1(self):
        pass
      def method2(self):
        pass
    ```
    This will produce the following docs:

    ```
    /Parent.md
      # method2
    /Child.md
      # method2
    ```

    When generating docs for a class's arributes, the `__mro__` is searched and
    the attribute will be skipped if this decorator is detected on the attribute
    on any class in the `__mro__`.

    Note: This is implemented by adding a hidden attribute on the object, so it
    cannot be used on objects which do not allow new attributes to be added. So
    this decorator must go *below* `@property`, `@classmethod`,
    or `@staticmethod`:

    ```
    class Example(object):
      @property
      @do_not_doc_inheritable
      def x(self):
        return self._x
    ```

    Args:
      obj: The class-attribute to hide from the generated docs.

    Returns:
      obj
    """
    setattr(obj, _DO_NOT_DOC_INHERITABLE, None)
    return obj


_FOR_SUBCLASS_IMPLEMENTERS = "_docs_tools_for_subclass_implementers"


def for_subclass_implementers(obj: T) -> T:
    """A decorator: Only generate docs for this method in the defining class.

    Also group this method's docs with and `@abstractmethod` in the class's docs.

    No docs will generated for this class attribute in sub-classes.

    The canonical use case for this is `tf.keras.layers.Layer.call`: It's a
    public method, essential for anyone implementing a subclass, but it should
    never be called directly.

    Works on method, or other class-attributes.

    When generating docs for a class's arributes, the `__mro__` is searched and
    the attribute will be skipped if this decorator is detected on the attribute
    on any **parent** class in the `__mro__`.

    For example:

    ```
    class Parent(object):
      @for_subclass_implementers
      def method1(self):
        pass
      def method2(self):
        pass

    class Child1(Parent):
      def method1(self):
        pass
      def method2(self):
        pass

    class Child2(Parent):
      def method1(self):
        pass
      def method2(self):
        pass
    ```

    This will produce the following docs:

    ```
    /Parent.md
      # method1
      # method2
    /Child1.md
      # method2
    /Child2.md
      # method2
    ```

    Note: This is implemented by adding a hidden attribute on the object, so it
    cannot be used on objects which do not allow new attributes to be added. So
    this decorator must go *below* `@property`, `@classmethod`,
    or `@staticmethod`:

    ```
    class Example(object):
      @property
      @for_subclass_implementers
      def x(self):
        return self._x
    ```

    Args:
      obj: The class-attribute to hide from the generated docs.

    Returns:
      obj
    """
    setattr(obj, _FOR_SUBCLASS_IMPLEMENTERS, None)
    return obj


do_not_doc_in_subclasses = for_subclass_implementers

_DOC_PRIVATE = "_docs_doc_private"


def doc_private(obj: T) -> T:
    """A decorator: Generates docs for private methods/functions.

    For example:

    ```
    class Try:

      @doc_controls.doc_private
      def _private(self):
        ...
    ```

    As a rule of thumb, private(beginning with `_`) methods/functions are
    not documented.

    This decorator allows to force document a private method/function.

    Args:
      obj: The class-attribute to hide from the generated docs.

    Returns:
      obj
    """

    setattr(obj, _DOC_PRIVATE, None)
    return obj


def should_doc_private(obj) -> bool:
    return hasattr(obj, _DOC_PRIVATE)


_DOC_IN_CURRENT_AND_SUBCLASSES = "_docs_doc_in_current_and_subclasses"


def doc_in_current_and_subclasses(obj: T) -> T:
    """Overrides `do_not_doc_in_subclasses` decorator.

    If this decorator is set on a child class's method whose parent's method
    contains `do_not_doc_in_subclasses`, then that will be overriden and the
    child method will get documented. All classes inherting from the child will
    also document that method.

    For example:

    ```
    class Parent:
      @do_not_doc_in_subclasses
      def method1(self):
        pass
      def method2(self):
        pass

    class Child1(Parent):
      @doc_in_current_and_subclasses
      def method1(self):
        pass
      def method2(self):
        pass

    class Child2(Parent):
      def method1(self):
        pass
      def method2(self):
        pass

    class Child11(Child1):
      pass
    ```

    This will produce the following docs:

    ```
    /Parent.md
      # method1
      # method2
    /Child1.md
      # method1
      # method2
    /Child2.md
      # method2
    /Child11.md
      # method1
      # method2
    ```

    Args:
      obj: The class-attribute to hide from the generated docs.

    Returns:
      obj
    """

    setattr(obj, _DOC_IN_CURRENT_AND_SUBCLASSES, None)
    return obj


def should_skip(obj) -> bool:
    """Returns true if docs generation should be skipped for this object.

    Checks for the `do_not_generate_docs` or `do_not_doc_inheritable` decorators.

    Args:
      obj: The object to document, or skip.

    Returns:
      True if the object should be skipped
    """
    if isinstance(obj, type):
        # For classes, only skip if the attribute is set on _this_ class.
        if _DO_NOT_DOC in obj.__dict__:
            return True
        else:
            return False

    # Unwrap fget if the object is a property
    if isinstance(obj, property):
        obj = obj.fget

    return hasattr(obj, _DO_NOT_DOC) or hasattr(obj, _DO_NOT_DOC_INHERITABLE)


def _unwrap_func(obj):
    # Unwrap fget if the object is a property or static method or classmethod.
    if isinstance(obj, property):
        return obj.fget

    if isinstance(obj, (classmethod, staticmethod)):
        return obj.__func__

    return obj


def is_builtin_def(obj: Any) -> bool:
    """Returns True if the class is defined in a builtin module."""
    builtin_modules = set(sys.builtin_module_names)
    if hasattr(sys, "stdlib_module_names"):  # Added in Python 3.10+
        builtin_modules |= sys.stdlib_module_names
    return obj.__module__ in builtin_modules


def is_pydantic_def(obj: Any) -> bool:
    """Returns True if the class is defined in the pydantic package."""
    return bool((module := getmodule(obj)) and (module.__package__ == "pydantic"))


def should_skip_class_attr(cls, name):
    """Returns true if docs should be skipped for this class attribute.

    Args:
      cls: The class the attribute belongs to.
      name: The name of the attribute.

    Returns:
      True if the attribute should be skipped.
    """
    # Skip if the attribute is inherited from a builtin type or pydantic.BaseModel
    for base in cls.__mro__:
        if (is_builtin_def(base) or is_pydantic_def(base)) and (name in base.__dict__):
            return True

    # Get the object with standard lookup, from the nearest
    # defining parent.
    try:
        obj = getattr(cls, name)
    except AttributeError:
        if name in ("name", "value"):
            # Avoid error caused by enum metaclasses in python3
            return True
        if issubclass(cls, pydantic.BaseModel) and (name in cls.model_fields):
            # We still want to document Pydantic model fields.
            # However, note that on class definition, fields in Pydantic models
            # are removed from the class namespace and are instead accessible
            # via the `cls.model_fields` lookup.
            return False
        raise

    # Unwrap fget if the object is a property
    obj = _unwrap_func(obj)

    # Skip if the object is decorated with `do_not_generate_docs` or
    # `do_not_doc_inheritable`
    if should_skip(obj):
        return True

    # Use __dict__ lookup to get the version defined in *this* class.
    obj = cls.__dict__.get(name, None)
    obj = _unwrap_func(obj)

    if obj is not None:
        # If not none, the object is defined in *this* class.
        # Do not skip if decorated with `for_subclass_implementers`.
        if hasattr(obj, _FOR_SUBCLASS_IMPLEMENTERS):
            return False

        # If object is defined in this class, then don't skip if decorated with
        # `doc_in_current_and_subclasses`.
        if hasattr(obj, _DOC_IN_CURRENT_AND_SUBCLASSES):
            return False

    # for each parent class
    parent_classes = getattr(cls, "__mro__", [])[1:]
    for parent in parent_classes:
        obj = getattr(parent, name, None)

        if obj is None:
            continue

        obj = _unwrap_func(obj)

        if hasattr(obj, _DOC_IN_CURRENT_AND_SUBCLASSES):
            return False

        # Skip if the parent's definition is decorated with `do_not_doc_inheritable`
        # or `for_subclass_implementers`
        if hasattr(obj, _DO_NOT_DOC_INHERITABLE):
            return True

        if hasattr(obj, _FOR_SUBCLASS_IMPLEMENTERS):
            return True

    # No blockng decorators --> don't skip
    return False


def decorate_all_class_attributes(decorator, cls, skip: Iterable[str]):
    """Applies `decorator` to every attribute defined in `cls`.

    Args:
      decorator: The decorator to apply.
      cls: The class to apply the decorator to.
      skip: A collection of attribute names that the decorator should not be
        aplied to.
    """
    skip = frozenset(skip)
    class_contents = list(cls.__dict__.items())

    for name, obj in class_contents:
        if name in skip:
            continue

        # Otherwise, exclude from documentation.
        if isinstance(obj, property):
            obj = obj.fget

        if isinstance(obj, (staticmethod, classmethod)):
            obj = obj.__func__

        try:
            decorator(obj)
        except AttributeError:
            pass
