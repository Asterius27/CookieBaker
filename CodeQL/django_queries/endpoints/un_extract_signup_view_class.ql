import python
import codeql_library.DjangoSession

Class getSignUpClass() {
    exists(Function f, Class cls |
        f = DjangoSession::getSignUpFormCall().getScope()
        and cls.getAMethod() = f
        and result = cls)
    or exists(Class cls |
        cls.getAStmt().contains(DjangoSession::getSignUpFormCall().asExpr())
        and result = cls)
}

Class getSignUpClassView(Class cls) {
    if cls = DjangoSession::getClassViews()
    then result = cls
    else exists(Class cl |
        cl.getABase().toString() = cls.getName()
        and result = getSignUpClassView(cl))
}

from Class cls
where cls = getSignUpClass()
select cls, cls.getLocation()
