import python
import codeql_library.FlaskLogin

from Class cls, Call c, Function f
where (FlaskLogin::isModelClass(cls)
        or FlaskLogin::isModelFunction(cls))
    and exists(cls.getLocation().getFile().getRelativePath())
    and (cls.getClassObject().hasAttribute("password")
        or cls.getClassObject().hasAttribute("passwd")
        or cls.getClassObject().hasAttribute("pwd"))
    and c.getFunc().(Name).getId() = cls.getName()
    and f = c.getScope()
    and not f.isMethod()
select f, f.getLocation()
