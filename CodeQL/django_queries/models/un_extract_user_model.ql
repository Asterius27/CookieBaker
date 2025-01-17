import python
import codeql_library.DjangoSession

from Class cls
where ((cls.getABase() = API::moduleImport("django").getMember("db").getMember("models").getMember("Model").getAValueReachableFromSource().asExpr()
            and (cls.getName().toLowerCase().matches("%user")
                or cls.getName().toLowerCase().matches("user%")
                or cls.getName().toLowerCase().matches("%users")
                or cls.getName().toLowerCase().matches("users%")))
        or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("AbstractUser").getAValueReachableFromSource().asExpr()
        or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("base_user").getMember("AbstractBaseUser").getAValueReachableFromSource().asExpr()
        or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getMember("User").getAValueReachableFromSource().asExpr())
    and exists(cls.getLocation().getFile().getRelativePath())
select cls, cls.getLocation()
