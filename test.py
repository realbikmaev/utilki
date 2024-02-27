class MyClass:
    def __init__(self):
        self._data = {}

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            self._data[name] = 0
            return 0

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def __iadd__(self, other):
        if isinstance(other, int):
            setattr(self, self._name, getattr(self, self._name) + other)
        else:
            raise TypeError(
                f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self


# Create an instance of MyClass
a = MyClass()

# Set the name of the attribute to use with the += operator
a._name = "x"

# Use the += operator with the attribute
a += 1
print(a.x)  # Output: 1

# Use the += operator with a non-integer
try:
    a += "abc"
except TypeError as e:
    print(
        e
    )  # Output: unsupported operand type(s) for +=: 'MyClass' and 'str'
