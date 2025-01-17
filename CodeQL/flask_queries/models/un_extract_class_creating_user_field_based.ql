import python
import codeql_library.FlaskLogin

from Class cls, Call c, Function f, Class cl
where (FlaskLogin::isModelClass(cls)
        or FlaskLogin::isModelFunction(cls))
    and exists(cls.getLocation().getFile().getRelativePath())
    and (cls.getClassObject().hasAttribute("password")
        or cls.getClassObject().hasAttribute("passwd")
        or cls.getClassObject().hasAttribute("pwd"))
    and c.getFunc().(Name).getId() = cls.getName()
    and f = c.getScope()
    and f.isMethod()
    and cl.getAMethod() = f
select cl, cl.getLocation()
