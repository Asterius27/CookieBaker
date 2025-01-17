import python
import codeql_library.DjangoSession

Function functionCreatingUserCustomModels() {
    exists(Class cls, Call c, Function f |
            ((cls.getABase() = API::moduleImport("django").getMember("db").getMember("models").getMember("Model").getAValueReachableFromSource().asExpr()
                and (cls.getName().toLowerCase().matches("%user")
                    or cls.getName().toLowerCase().matches("user%")
                    or cls.getName().toLowerCase().matches("%users")
                    or cls.getName().toLowerCase().matches("users%")))
            or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("AbstractUser").getAValueReachableFromSource().asExpr()
            or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("base_user").getMember("AbstractBaseUser").getAValueReachableFromSource().asExpr()
            or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("User").getAValueReachableFromSource().asExpr())
        and exists(cls.getLocation().getFile().getRelativePath())
        and c.getFunc().(Name).getId() = cls.getName()
        and f = c.getScope()
        and not f.isMethod()
        and result = f)
}

Function functionCreatingUser() {
    exists(Function f |
        f = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("User").getAValueReachableFromSource().getScope()
        and not f.isMethod()
        and result = f)
}

from Function f
where f = functionCreatingUser()
    or f = functionCreatingUserCustomModels()
select f, f.getLocation()
