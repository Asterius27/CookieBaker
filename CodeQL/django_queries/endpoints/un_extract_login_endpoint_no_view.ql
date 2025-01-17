import python
import codeql_library.DjangoSession

from string str, API::CallNode node
where exists(StringLiteral strr | 
        strr.getText() = "django.contrib.auth.urls"
        and node = DjangoSession::getURLDefinitions().getACall()
        and str = DjangoSession::getEndpoint(node) + "login/"
        and node.asExpr().contains(strr))
    or exists(DataFlow::Node views | 
        views = API::moduleImport("django").getMember("contrib").getMember("auth").getMember("views").getMember("LoginView").getAValueReachableFromSource()
        and not views.asExpr() instanceof ImportMember
        and exists(views.asCfgNode())
        and exists(views.getLocation().getFile().getRelativePath())
        and node = DjangoSession::getURLDefinitions().getACall()
        and str = DjangoSession::getEndpoint(node)
        and node.asExpr().contains(views.asExpr()))
select DjangoSession::calculateURLPrefix(node) + str
