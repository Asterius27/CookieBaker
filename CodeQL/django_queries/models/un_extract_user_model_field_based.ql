import python
import codeql_library.DjangoSession

from Class cls
where cls.getABase() = API::moduleImport("django").getMember("db").getMember("models").getMember("Model").getAValueReachableFromSource().asExpr()
    and (cls.getClassObject().hasAttribute("password")
        or cls.getClassObject().hasAttribute("passwd")
        or cls.getClassObject().hasAttribute("pwd"))
    and exists(cls.getLocation().getFile().getRelativePath())
select cls, cls.getLocation()
