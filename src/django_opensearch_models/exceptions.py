class DjangoOpenSearchModelsError(Exception):
    pass


class VariableLookupError(DjangoOpenSearchModelsError):
    pass


class RedeclaredFieldError(DjangoOpenSearchModelsError):
    pass


class ModelFieldNotMappedError(DjangoOpenSearchModelsError):
    pass
