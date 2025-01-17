import python
import codeql_library.DjangoSession

Class getLoginClass() {
    exists(Function f, Class cls |
        f = DjangoSession::getLoginFunctionCall().getScope()
        and cls.getAMethod() = f
        and result = cls)
    or exists(Class cls, DataFlow::Node view | 
        view = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("views").getMember("LoginView").getAValueReachableFromSource()
        and cls.getABase() = view.asExpr()
        and result = cls)
}

Class getLoginClassView(Class cls) {
    if cls = DjangoSession::getClassViews()
    then result = cls
    else exists(Class cl |
        cl.getABase().toString() = cls.getName()
        and result = getLoginClassView(cl))
}

from Class cls
where cls = getLoginClass()
select cls, cls.getLocation()
