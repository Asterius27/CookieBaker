import python
import codeql_library.FlaskLogin

Function getLoginFunctionView() {
    exists(DataFlow::Node node |
        (node = API::moduleImport("flask_login").getMember("login_user").getAValueReachableFromSource()
            or node = API::moduleImport("flask_login").getMember("utils").getMember("login_user").getAValueReachableFromSource())
        and not node.asExpr() instanceof ImportMember
        and exists(node.asCfgNode())
        and exists(node.getLocation().getFile().getRelativePath())
        and result = node.getScope())
}

from Function f
where f = getLoginFunctionView()
select f, f.getLocation()
