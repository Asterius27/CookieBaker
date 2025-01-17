import python
import codeql_library.FlaskLogin

from Class cls
where (FlaskLogin::isModelClass(cls)
        or FlaskLogin::isModelFunction(cls))
    and exists(cls.getLocation().getFile().getRelativePath())
    and (cls.getName().toLowerCase().matches("%user")
        or cls.getName().toLowerCase().matches("user%")
        or cls.getName().toLowerCase().matches("%users")
        or cls.getName().toLowerCase().matches("users%"))
select cls, cls.getLocation()
