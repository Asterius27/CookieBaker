import python
import codeql_library.DjangoSession

Class classCreatingUserCustomModels() {
    exists(Class cls, Call c, Function f, Class cl |
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
        and f.isMethod()
        and cl.getAMethod() = f
        and result = cl)
}

Class classCreatingUser() {
    exists(Class cls, Function f |
        f = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("User").getAValueReachableFromSource().getScope()
        and f.isMethod()
        and cls.getAMethod() = f
        and result = cls)
}

from Class cl
where cl = classCreatingUser()
    or cl = classCreatingUserCustomModels()
select cl, cl.getLocation()
