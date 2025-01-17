import python
import codeql_library.FlaskLogin

Class getLoginClass() {
    exists(DataFlow::Node node, Function f, Class cls |
        (node = API::moduleImport("flask_login").getMember("login_user").getAValueReachableFromSource()
            or node = API::moduleImport("flask_login").getMember("utils").getMember("login_user").getAValueReachableFromSource())
        and not node.asExpr() instanceof ImportMember
        and exists(node.asCfgNode())
        and exists(node.getLocation().getFile().getRelativePath())
        and f = node.getScope()
        and cls.getAMethod() = f
        and result = cls)
}

Class getLoginClassView(Class cls) {
    if cls = FlaskLogin::getClassViews()
    then result = cls
    else exists(Class cl |
        cl.getABase().toString() = cls.getName()
        and result = getLoginClassView(cl))
}

from Class cls
where cls = getLoginClass()
select cls, cls.getLocation()
