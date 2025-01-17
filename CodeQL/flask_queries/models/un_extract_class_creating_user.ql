import python
import codeql_library.FlaskLogin

from Class cls, Call c, Function f, Class cl
where (FlaskLogin::isModelClass(cls)
        or FlaskLogin::isModelFunction(cls))
    and exists(cls.getLocation().getFile().getRelativePath())
    and (cls.getName().toLowerCase().matches("%user")
        or cls.getName().toLowerCase().matches("user%")
        or cls.getName().toLowerCase().matches("%users")
        or cls.getName().toLowerCase().matches("users%"))
    and c.getFunc().(Name).getId() = cls.getName()
    and f = c.getScope()
    and f.isMethod()
    and cl.getAMethod() = f
select cl, cl.getLocation()
