import python
import codeql_library.FlaskLogin

Class getSignUpClass() {
    exists(Function f, Class cls, Name name, Class form |
        form = FlaskLogin::getSignUpFormClass()
        and form.getName() = name.getId()
        and f = name.getScope()
        and cls.getAMethod() = f
        and result = cls)
    or exists(DataFlow::Node node, Function f, Class cls | 
        (node = API::moduleImport("flask").getMember("request").getMember("form").getSubscript("password").getAValueReachableFromSource()
            or node = API::moduleImport("flask").getMember("request").getMember("form").getSubscript("password1").getAValueReachableFromSource()
            or exists (API::Node n |
                n = API::moduleImport("flask").getMember("request").getMember("form").getMember("get")
                and (n.getParameter(0).getAValueReachingSink().asExpr().(StringLiteral).getText() = "password"
                    or n.getParameter(0).getAValueReachingSink().asExpr().(StringLiteral).getText() = "password1")
                and node = n.getAValueReachableFromSource()))
        and not exists(DataFlow::Node n |
            (n = API::moduleImport("flask_login").getMember("login_user").getAValueReachableFromSource()
                or n = API::moduleImport("flask_login").getMember("utils").getMember("login_user").getAValueReachableFromSource())
            and n.getScope() = node.getScope())
        and f = node.getScope()
        and cls.getAMethod() = f
        and result = cls)
}

Class getSignUpClassView(Class cls) {
    if cls = FlaskLogin::getClassViews()
    then result = cls
    else exists(Class cl |
        cl.getABase().toString() = cls.getName()
        and result = getSignUpClassView(cl))
}

from Class cls
where cls = getSignUpClass()
select cls, cls.getLocation()
