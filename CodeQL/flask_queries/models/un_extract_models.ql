import python
import codeql_library.FlaskLogin

from Class cls
where (FlaskLogin::isModelClass(cls)
        or FlaskLogin::isModelFunction(cls))
    and exists(cls.getLocation().getFile().getRelativePath())
select cls, cls.getLocation()
