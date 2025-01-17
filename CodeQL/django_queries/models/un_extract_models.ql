import python
import codeql_library.DjangoSession

from Class cls
where cls.getABase() = API::moduleImport("django").getMember("db").getMember("models").getMember("Model").getAValueReachableFromSource().asExpr()
    or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getAMember().getAValueReachableFromSource().asExpr()
    or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("base_user").getAMember().getAValueReachableFromSource().asExpr()
    or cls.getABase() = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("models").getAMember().getAValueReachableFromSource().asExpr()
select cls, cls.getLocation()
