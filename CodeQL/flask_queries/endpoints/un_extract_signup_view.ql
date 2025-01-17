import python
import codeql_library.FlaskLogin

Function getSignUpFunctionView() {
    exists(Class cls, Name name |
        cls = FlaskLogin::getSignUpFormClass()
        and cls.getName() = name.getId()
        and result = name.getScope())
    or exists(DataFlow::Node node | 
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
        and result = node.getScope())
}

from Function f
where f = getSignUpFunctionView()
select f, f.getLocation()
