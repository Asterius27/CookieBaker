import python
import codeql_library.DjangoSession

from Class cls, Call c, Function f
where cls.getABase() = API::moduleImport("django").getMember("db").getMember("models").getMember("Model").getAValueReachableFromSource().asExpr()
    and exists(cls.getLocation().getFile().getRelativePath())
    and (cls.getClassObject().hasAttribute("password")
        or cls.getClassObject().hasAttribute("passwd")
        or cls.getClassObject().hasAttribute("pwd"))
    and c.getFunc().(Name).getId() = cls.getName()
    and f = c.getScope()
    and not f.isMethod()
select f, f.getLocation()
